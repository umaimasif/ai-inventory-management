"""Product business logic, including stock adjustments."""
from app.models.product import Product
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.errors import ConflictError, NotFoundError, ValidationError


class ProductService:
    def __init__(
        self,
        products: ProductRepository,
        categories: CategoryRepository,
        suppliers: SupplierRepository,
    ) -> None:
        self._products = products
        self._categories = categories
        self._suppliers = suppliers

    def list(self) -> list[Product]:
        return self._products.list(limit=500)

    def get(self, product_id: int) -> Product:
        product = self._products.get(product_id)
        if product is None:
            raise NotFoundError("Product not found")
        return product

    def _validate_refs(self, category_id: int | None, supplier_id: int | None) -> None:
        if category_id is not None and self._categories.get(category_id) is None:
            raise ValidationError("Referenced category does not exist")
        if supplier_id is not None and self._suppliers.get(supplier_id) is None:
            raise ValidationError("Referenced supplier does not exist")

    def create(self, data: ProductCreate) -> Product:
        if self._products.get_by_sku(data.sku):
            raise ConflictError("A product with that SKU already exists")
        self._validate_refs(data.category_id, data.supplier_id)
        return self._products.add(Product(**data.model_dump()))

    def update(self, product_id: int, data: ProductUpdate) -> Product:
        product = self.get(product_id)
        changes = data.model_dump(exclude_unset=True)

        if "sku" in changes:
            existing = self._products.get_by_sku(changes["sku"])
            if existing and existing.id != product_id:
                raise ConflictError("A product with that SKU already exists")

        self._validate_refs(changes.get("category_id"), changes.get("supplier_id"))

        for field, value in changes.items():
            setattr(product, field, value)
        return self._products.save(product)

    def delete(self, product_id: int) -> None:
        self._products.soft_delete(self.get(product_id))

    def adjust_stock(self, product_id: int, delta: int) -> Product:
        """Add or remove stock. Refuses to drive stock negative."""
        product = self.get(product_id)
        new_qty = product.stock_quantity + delta
        if new_qty < 0:
            raise ValidationError(
                f"Adjustment would make stock negative "
                f"(current {product.stock_quantity}, delta {delta})"
            )
        product.stock_quantity = new_qty
        return self._products.save(product)
