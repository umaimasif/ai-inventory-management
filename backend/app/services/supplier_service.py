"""Supplier business logic."""
from app.models.supplier import Supplier
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.supplier import SupplierCreate, SupplierUpdate
from app.services.errors import NotFoundError


class SupplierService:
    def __init__(self, repo: SupplierRepository) -> None:
        self._repo = repo

    def list(self) -> list[Supplier]:
        return self._repo.list(limit=500)

    def get(self, supplier_id: int) -> Supplier:
        supplier = self._repo.get(supplier_id)
        if supplier is None:
            raise NotFoundError("Supplier not found")
        return supplier

    def create(self, data: SupplierCreate) -> Supplier:
        return self._repo.add(Supplier(**data.model_dump()))

    def update(self, supplier_id: int, data: SupplierUpdate) -> Supplier:
        supplier = self.get(supplier_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(supplier, field, value)
        return self._repo.save(supplier)

    def delete(self, supplier_id: int) -> None:
        self._repo.soft_delete(self.get(supplier_id))
