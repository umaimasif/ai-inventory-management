"""Customer business logic."""
from app.models.customer import Customer
from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.services.errors import NotFoundError, ValidationError


class CustomerService:
    def __init__(self, repo: CustomerRepository) -> None:
        self._repo = repo

    def list(self) -> list[Customer]:
        return self._repo.list(limit=500)

    def get(self, customer_id: int) -> Customer:
        customer = self._repo.get(customer_id)
        if customer is None:
            raise NotFoundError("Customer not found")
        return customer

    def create(self, data: CustomerCreate) -> Customer:
        return self._repo.add(Customer(**data.model_dump()))

    def update(self, customer_id: int, data: CustomerUpdate) -> Customer:
        customer = self.get(customer_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(customer, field, value)
        return self._repo.save(customer)

    def delete(self, customer_id: int) -> None:
        customer = self.get(customer_id)
        if customer.is_walkin:
            raise ValidationError("The walk-in customer cannot be deleted")
        self._repo.soft_delete(customer)
