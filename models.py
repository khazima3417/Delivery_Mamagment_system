from dataclasses import dataclass
@dataclass
class Driver:
    driver_id: str
    name: str
    zone: str
    available: bool
    rating: float
@dataclass
class Delivery:
    task_id: str
    customer: str
    zone: str
    distance: float
    order_amount: float
    priority: str
    status: str
    driver_id: str = ""
    delivery_charge: float = 0
    driver_earning: float = 0