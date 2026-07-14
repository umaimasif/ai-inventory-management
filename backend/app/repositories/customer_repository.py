"""Customer data-access."""
from sqlalchemy import select

from app.models.customer import Customer
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    model = Customer

    def get_walkin(self) -> Customer | None:
        """Return the default walk-in customer, if it exists."""
        stmt = select(Customer).where(
            Customer.is_walkin.is_(True), Customer.is_deleted.is_(False)
        )
        return self._db.scalar(stmt)

    def get_or_create_walkin(self) -> Customer:
        """Return the walk-in customer, creating it on first use."""
        existing = self.get_walkin()
        if existing:
            return existing
        walkin = Customer(name="Walk-in", is_walkin=True)
        return self.add(walkin)
