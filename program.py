import json
from models import Driver, Delivery
# CUSTOM ERROR HANDLING
class DeliveryError(Exception):
    pass

class ValidationError(DeliveryError):
    pass
class DriverError(DeliveryError):
    pass
class TaskError(DeliveryError):
    pass
class StatusTransitionError(DeliveryError):
    pass
# LOAD JSON DATA
def load_data(filename):
    try:
        with open(filename, "r") as file:
            data = json.load(file)
        if "drivers" not in data:
            raise ValidationError("Drivers data is missing.")
        if "deliveries" not in data:
            raise ValidationError("Deliveries data is missing.")
        return data
    except FileNotFoundError:
        print("Error: data.json file not found.")
        return None
    except json.JSONDecodeError:
        print("Error: JSON file format is invalid.")
        return None
    except PermissionError:
        print("Error: Permission denied.")
        return None
    except ValidationError as error:
        print("Validation Error:", error)
        return None
# CREATE DRIVER OBJECTS
def create_drivers(data):
    drivers = {}
    try:
        for driver_id, value in data["drivers"].items():
            driver = Driver(
                driver_id=driver_id,
                name=value["name"],
                zone=value["zone"],
                available=value["available"],
                rating=float(value["rating"])
            )
            drivers[driver_id] = driver
    except KeyError as error:
        raise ValidationError(
            f"Missing driver field: {error}"
        )
    except (TypeError, ValueError) as error:
        raise ValidationError(
            f"Invalid driver data: {error}"
        )
    return drivers
# CREATE DELIVERY OBJECTS
def create_deliveries(data):
    deliveries = []
    try:
        for value in data["deliveries"]:
            delivery = Delivery(
                task_id=value["id"],
                customer=value["customer"],
                zone=value["zone"],
                distance=float(value["distance"]),
                order_amount=float(value["order_amount"]),
                priority=value["priority"],
                status=value["status"],
                driver_id=value.get("driver_id", "")
            )
            deliveries.append(delivery)
    except KeyError as error:
        raise ValidationError(
            f"Missing delivery field: {error}"
        )
    except (TypeError, ValueError) as error:
        raise ValidationError(
            f"Invalid delivery data: {error}"
        )
    return deliveries
# VALIDATE DELIVERY
def validate_delivery(delivery):
    if delivery.distance < 0:
        raise ValidationError(
            f"{delivery.task_id}: Distance cannot be negative."
        )
    if delivery.order_amount < 0:
        raise ValidationError(
            f"{delivery.task_id}: Order amount cannot be negative."
        )
    if delivery.priority not in ["normal", "urgent"]:
        raise ValidationError(
            f"{delivery.task_id}: Invalid priority."
        )
    if delivery.status not in [
        "pending",
        "assigned",
        "picked_up",
        "delivered",
        "failed"
    ]:
        raise ValidationError(
            f"{delivery.task_id}: Invalid status."
        )
    return True
# FIND DELIVERY
def get_delivery(task_id, deliveries):
    for delivery in deliveries:
        if delivery.task_id == task_id:
            return delivery
    raise TaskError(
        f"Task {task_id} not found."
    )
# FIND BEST DRIVER
def assign_driver(task_id, deliveries, drivers):
    delivery = get_delivery(
        task_id,
        deliveries
    )
    if delivery.status != "pending":
        raise TaskError(
            f"{task_id} is not pending."
        )
    available_drivers = [
        driver
        for driver in drivers.values()
        if driver.available
        and driver.zone == delivery.zone
    ]
    if not available_drivers:
        raise DriverError(
            f"No available driver in zone {delivery.zone}."
        )
# Highest rating driver
    best_driver = max(
        available_drivers,
        key=lambda driver: driver.rating
    )
    delivery.driver_id = best_driver.driver_id
    delivery.status = "assigned"
    best_driver.available = False
    return best_driver
# CALCULATE DELIVERY CHARGE
def calculate_charge(distance, priority, **options):
    base_charge = options.get(
        "base_charge",
        5
    )
    if distance <= 5:
        rate = 1
    elif distance <= 10:
        rate = 1.5
    else:
        rate = 2
    charge = base_charge + (distance * rate)
    if priority == "urgent":
        charge = charge * 1.25
    return charge
# DRIVER EARNING
def calculate_earning(distance, order_amount, **options):
    base_earning = options.get(
        "base_earning",
        3
    )
    earning = base_earning + (distance * 0.8)
    if order_amount >= 150:
        earning = earning * 1.10
    return earning
# PROCESS DELIVERY
def process_delivery(delivery):
    delivery.delivery_charge = calculate_charge(
        delivery.distance,
        delivery.priority
    )
    delivery.driver_earning = calculate_earning(
        delivery.distance,
        delivery.order_amount
    )
# UPDATE STATUS
def update_status(task_id, new_status, deliveries, drivers):
    delivery = get_delivery(
        task_id,
        deliveries
    )
    allowed_status = {
        "pending": ["assigned"],
        "assigned": ["picked_up", "failed"],
        "picked_up": ["delivered", "failed"],
        "delivered": [],
        "failed": []
    }
    if new_status not in allowed_status:
        raise StatusTransitionError(
            "Invalid status."
        )
    if new_status not in allowed_status[delivery.status]:
        raise StatusTransitionError(
            f"Cannot change {delivery.status} "
            f"to {new_status}."
        )
    delivery.status = new_status
# Driver becomes available again
    if new_status in ["delivered", "failed"]:
        if delivery.driver_id in drivers:
            drivers[
                delivery.driver_id
            ].available = True
# DISPLAY DELIVERY
def show_delivery(delivery):
    print("Task ID:", delivery.task_id)
    print("Customer:", delivery.customer)
    print("Zone:", delivery.zone)
    print("Distance:", delivery.distance, "km")
    print("Order Amount: $", delivery.order_amount)
    print("Priority:", delivery.priority)
    print("Status:", delivery.status)
    print("Driver ID:", delivery.driver_id)
    print(
        "Delivery Charge: $",
        round(delivery.delivery_charge, 2)
    )
    print(
        "Driver Earning: $",
        round(delivery.driver_earning, 2)
    )
def save_data(filename, drivers, deliveries):
    data = {
        "drivers": {
            driver_id: {
                "name": driver.name,
                "zone": driver.zone,
                "available": driver.available,
                "rating": driver.rating
            }
            for driver_id, driver in drivers.items()
        },
        "deliveries": [
            {
                "id": delivery.task_id,
                "customer": delivery.customer,
                "zone": delivery.zone,
                "distance": delivery.distance,
                "order_amount": delivery.order_amount,
                "priority": delivery.priority,
                "status": delivery.status,
                "driver_id": delivery.driver_id,
                "delivery_charge": delivery.delivery_charge,
                "driver_earning": delivery.driver_earning
            }
            for delivery in deliveries
        ]
    }
    try:
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)
        print("\nData saved successfully.")
    except (PermissionError, OSError) as error:
        print("Save Error:", error)
# MAIN PROGRAM
def main():
    print("================================")
    print(" DELIVERY MANAGEMENT SYSTEM")
    print("================================")
    data = load_data("data.json")
    if data is None:
        return
    try:
        drivers = create_drivers(data)
        deliveries = create_deliveries(data)
    except DeliveryError as error:
        print("Error:", error)
        return
    print("===== VALIDATION =====")
    for delivery in deliveries:
        try:
            validate_delivery(delivery)
            print(
                delivery.task_id,
                "is valid."
            )
        except ValidationError as error:
            print("Error:", error)
    print("\n===== DRIVER ASSIGNMENT =====")
    for delivery in deliveries:
        try:
            driver = assign_driver(
                delivery.task_id,
                deliveries,
                drivers
            )
            print(
                delivery.task_id,
                "->",
                driver.name
            )
        except DeliveryError as error:
            print(
                delivery.task_id,
                ":",
                error
            )
    print("\n===== CALCULATIONS =====")
    for delivery in deliveries:
        try:
            process_delivery(delivery)
            print(
                delivery.task_id,
                "Charge = $",
                round(
                    delivery.delivery_charge,
                    2
                )
            )
        except DeliveryError as error:
            print("Error:", error)
    print("\n===== STATUS UPDATE =====")
    try:
        update_status(
            "TASK001",
            "picked_up",
            deliveries,
            drivers
        )
        print(
            "TASK001 -> picked_up"
        )
        update_status(
            "TASK001",
            "delivered",
            deliveries,
            drivers
        )
        print(
            "TASK001 -> delivered"
        )
    except DeliveryError as error:
        print("Status Error:", error)
    print("\n===== ALL DELIVERIES =====")
    for delivery in deliveries:
        show_delivery(delivery)
    save_data(
        "data.json",
        drivers,
        deliveries
    )
    print("\nProgram completed.")
if __name__ == "__main__":
    main()