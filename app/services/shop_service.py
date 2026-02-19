from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.models.shop import Shop, ShopCategory
from app.models.product import Product
from app.models.order import Order
from app.schemas.shop import ShopCreate, ShopUpdate, ShopCategoryCreate, ShopCategoryUpdate


class ShopCategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ShopCategoryCreate) -> ShopCategory:
        category = ShopCategory(**data.model_dump())
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def get_by_id(self, category_id: int) -> Optional[ShopCategory]:
        result = await self.db.execute(
            select(ShopCategory).where(ShopCategory.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[ShopCategory]:
        result = await self.db.execute(
            select(ShopCategory).where(ShopCategory.name.ilike(f"%{name}%"))
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True) -> List[ShopCategory]:
        query = select(ShopCategory)
        if active_only:
            query = query.where(ShopCategory.is_active == True)
        query = query.order_by(ShopCategory.sort_order, ShopCategory.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_with_shop_count(self) -> List[Dict[str, Any]]:
        """Get categories with shop counts"""
        result = await self.db.execute(
            select(
                ShopCategory,
                func.count(Shop.id).label("shop_count")
            )
            .outerjoin(Shop, and_(Shop.category_id == ShopCategory.id, Shop.is_active == True))
            .where(ShopCategory.is_active == True)
            .group_by(ShopCategory.id)
            .order_by(ShopCategory.sort_order, ShopCategory.name)
        )
        rows = result.all()
        return [
            {
                "id": row[0].id,
                "name": row[0].name,
                "description": row[0].description,
                "icon": row[0].icon,
                "image_url": row[0].image_url,
                "is_active": row[0].is_active,
                "sort_order": row[0].sort_order,
                "created_at": row[0].created_at,
                "shop_count": row[1]
            }
            for row in rows
        ]

    async def update(self, category_id: int, data: ShopCategoryUpdate) -> Optional[ShopCategory]:
        category = await self.get_by_id(category_id)
        if not category:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def delete(self, category_id: int) -> bool:
        category = await self.get_by_id(category_id)
        if not category:
            return False
        await self.db.delete(category)
        await self.db.commit()
        return True


class ShopService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ShopCreate) -> Shop:
        shop = Shop(**data.model_dump())
        self.db.add(shop)
        await self.db.commit()
        await self.db.refresh(shop)
        return shop

    async def get_by_id(self, shop_id: int) -> Optional[Shop]:
        result = await self.db.execute(
            select(Shop).where(Shop.id == shop_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Shop]:
        result = await self.db.execute(
            select(Shop).where(Shop.name.ilike(f"%{name}%"))
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        category_id: Optional[int] = None,
        city: Optional[str] = None,
        search: Optional[str] = None,
        active_only: bool = True
    ) -> List[Shop]:
        query = select(Shop)

        if active_only:
            query = query.where(Shop.is_active == True)

        if category_id:
            query = query.where(Shop.category_id == category_id)

        if city:
            query = query.where(Shop.city.ilike(f"%{city}%"))

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Shop.name.ilike(search_term),
                    Shop.description.ilike(search_term)
                )
            )

        query = query.order_by(Shop.rating.desc(), Shop.name).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_category(self, category_id: int) -> List[Shop]:
        result = await self.db.execute(
            select(Shop)
            .where(and_(Shop.category_id == category_id, Shop.is_active == True))
            .order_by(Shop.rating.desc(), Shop.name)
        )
        return list(result.scalars().all())

    async def update(self, shop_id: int, data: ShopUpdate) -> Optional[Shop]:
        shop = await self.get_by_id(shop_id)
        if not shop:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(shop, field, value)
        await self.db.commit()
        await self.db.refresh(shop)
        return shop

    async def delete(self, shop_id: int) -> bool:
        shop = await self.get_by_id(shop_id)
        if not shop:
            return False
        await self.db.delete(shop)
        await self.db.commit()
        return True

    async def get_dashboard_stats(self, shop_id: int) -> Dict[str, Any]:
        """Get comprehensive dashboard stats for a shop owner"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Product stats
        total_products = await self.db.execute(
            select(func.count(Product.id))
            .where(Product.shop_id == shop_id)
        )
        total_products = total_products.scalar() or 0

        active_products = await self.db.execute(
            select(func.count(Product.id))
            .where(and_(Product.shop_id == shop_id, Product.is_active == True))
        )
        active_products = active_products.scalar() or 0

        low_stock = await self.db.execute(
            select(func.count(Product.id))
            .where(and_(
                Product.shop_id == shop_id,
                Product.is_active == True,
                Product.quantity <= Product.min_stock_level,
                Product.quantity > 0
            ))
        )
        low_stock = low_stock.scalar() or 0

        out_of_stock = await self.db.execute(
            select(func.count(Product.id))
            .where(and_(
                Product.shop_id == shop_id,
                Product.is_active == True,
                Product.quantity == 0
            ))
        )
        out_of_stock = out_of_stock.scalar() or 0

        # Inventory value
        inv_value = await self.db.execute(
            select(func.sum(Product.price * Product.quantity))
            .where(and_(Product.shop_id == shop_id, Product.is_active == True))
        )
        inventory_value = inv_value.scalar() or 0

        # Order stats
        total_orders = await self.db.execute(
            select(func.count(Order.id))
            .where(Order.shop_id == shop_id)
        )
        total_orders = total_orders.scalar() or 0

        pending_orders = await self.db.execute(
            select(func.count(Order.id))
            .where(and_(Order.shop_id == shop_id, Order.status == "pending"))
        )
        pending_orders = pending_orders.scalar() or 0

        today_orders = await self.db.execute(
            select(func.count(Order.id))
            .where(and_(Order.shop_id == shop_id, Order.created_at >= today))
        )
        today_orders = today_orders.scalar() or 0

        # Revenue
        total_revenue = await self.db.execute(
            select(func.sum(Order.total_amount))
            .where(and_(Order.shop_id == shop_id, Order.status != "cancelled"))
        )
        total_revenue = total_revenue.scalar() or 0

        today_revenue = await self.db.execute(
            select(func.sum(Order.total_amount))
            .where(and_(
                Order.shop_id == shop_id,
                Order.status != "cancelled",
                Order.created_at >= today
            ))
        )
        today_revenue = today_revenue.scalar() or 0

        # Unique customers
        total_customers = await self.db.execute(
            select(func.count(func.distinct(Order.customer_email)))
            .where(Order.shop_id == shop_id)
        )
        total_customers = total_customers.scalar() or 0

        return {
            "total_products": total_products,
            "active_products": active_products,
            "low_stock_count": low_stock,
            "out_of_stock_count": out_of_stock,
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "today_orders": today_orders,
            "total_revenue": round(total_revenue, 2),
            "today_revenue": round(today_revenue, 2),
            "total_customers": total_customers,
            "inventory_value": round(inventory_value, 2)
        }

    async def update_shop_metrics(self, shop_id: int, order_amount: float):
        """Update shop metrics after an order"""
        shop = await self.get_by_id(shop_id)
        if shop:
            shop.total_orders += 1
            shop.total_revenue += order_amount
            await self.db.commit()


# Default categories to seed on startup
DEFAULT_SHOP_CATEGORIES = [
    {"name": "Grocery", "description": "Fresh fruits, vegetables, dairy, and daily essentials", "icon": "🛒", "is_perishable": True, "sort_order": 1},
    {"name": "Beauty & Cosmetics", "description": "Makeup, skincare, haircare, and beauty products", "icon": "💄", "is_perishable": True, "sort_order": 2},
    {"name": "Fashion & Clothing", "description": "Men's, women's, and kids' apparel", "icon": "👗", "is_perishable": False, "sort_order": 3},
    {"name": "Footwear", "description": "Shoes, sandals, sneakers, and sports footwear", "icon": "👟", "is_perishable": False, "sort_order": 4},
    {"name": "Electronics", "description": "Mobiles, laptops, TVs, and gadgets", "icon": "📱", "is_perishable": False, "sort_order": 5},
    {"name": "Sports & Fitness", "description": "Sports equipment, gym gear, and fitness accessories", "icon": "⚽", "is_perishable": False, "sort_order": 6},
    {"name": "Home & Kitchen", "description": "Home decor, kitchenware, and appliances", "icon": "🏠", "is_perishable": False, "sort_order": 7},
    {"name": "Books & Stationery", "description": "Books, notebooks, pens, and office supplies", "icon": "📚", "is_perishable": False, "sort_order": 8},
    {"name": "Health & Wellness", "description": "Medicines, supplements, and healthcare products", "icon": "💊", "is_perishable": True, "sort_order": 9},
    {"name": "Jewelry & Accessories", "description": "Jewelry, watches, bags, and accessories", "icon": "💎", "is_perishable": False, "sort_order": 10},
]


async def create_default_categories(db: AsyncSession):
    """Create default shop categories if they don't exist"""
    for cat_data in DEFAULT_SHOP_CATEGORIES:
        # Check if category already exists
        result = await db.execute(
            select(ShopCategory).where(ShopCategory.name == cat_data["name"])
        )
        existing = result.scalar_one_or_none()

        if not existing:
            category = ShopCategory(**cat_data)
            db.add(category)

    await db.commit()
    print("✓ Default shop categories initialized")


# Default shops with products for each category
DEFAULT_SHOPS_DATA = {
    "Grocery": {
        "shop": {"name": "Fresh Mart", "description": "Your daily grocery needs", "city": "Mumbai", "owner_name": "Ramesh Kumar", "owner_email": "freshmart@demo.com"},
        "products": [
            {"name": "Basmati Rice (5kg)", "price": 450, "cost_price": 380, "quantity": 100},
            {"name": "Toor Dal (1kg)", "price": 180, "cost_price": 150, "quantity": 80},
            {"name": "Sunflower Oil (1L)", "price": 160, "cost_price": 130, "quantity": 60},
            {"name": "Whole Wheat Atta (5kg)", "price": 280, "cost_price": 230, "quantity": 90},
            {"name": "Sugar (1kg)", "price": 50, "cost_price": 42, "quantity": 150},
        ]
    },
    "Beauty & Cosmetics": {
        "shop": {"name": "Glow Studio", "description": "Premium beauty products", "city": "Delhi", "owner_name": "Priya Sharma", "owner_email": "glowstudio@demo.com"},
        "products": [
            {"name": "Lakme Lipstick Red", "price": 350, "cost_price": 220, "quantity": 40},
            {"name": "Face Wash Neem", "price": 180, "cost_price": 120, "quantity": 60},
            {"name": "Hair Serum 100ml", "price": 450, "cost_price": 300, "quantity": 35},
            {"name": "Moisturizer SPF 30", "price": 399, "cost_price": 260, "quantity": 50},
            {"name": "Kajal Pencil", "price": 150, "cost_price": 90, "quantity": 80},
        ]
    },
    "Fashion & Clothing": {
        "shop": {"name": "Style Hub", "description": "Trendy fashion for everyone", "city": "Bangalore", "owner_name": "Amit Patel", "owner_email": "stylehub@demo.com"},
        "products": [
            {"name": "Cotton Kurta Men", "price": 799, "cost_price": 450, "quantity": 30},
            {"name": "Denim Jeans Women", "price": 1299, "cost_price": 750, "quantity": 25},
            {"name": "Printed T-Shirt", "price": 499, "cost_price": 280, "quantity": 50},
            {"name": "Formal Shirt Men", "price": 999, "cost_price": 600, "quantity": 35},
            {"name": "Palazzo Pants", "price": 699, "cost_price": 400, "quantity": 40},
        ]
    },
    "Footwear": {
        "shop": {"name": "Foot Palace", "description": "Comfort for your feet", "city": "Chennai", "owner_name": "Suresh Iyer", "owner_email": "footpalace@demo.com"},
        "products": [
            {"name": "Running Shoes", "price": 2499, "cost_price": 1600, "quantity": 20},
            {"name": "Leather Sandals", "price": 899, "cost_price": 550, "quantity": 35},
            {"name": "Canvas Sneakers", "price": 1299, "cost_price": 800, "quantity": 30},
            {"name": "Formal Shoes Men", "price": 1999, "cost_price": 1200, "quantity": 25},
            {"name": "Flip Flops", "price": 299, "cost_price": 150, "quantity": 60},
        ]
    },
    "Electronics": {
        "shop": {"name": "Tech Zone", "description": "Latest gadgets and electronics", "city": "Hyderabad", "owner_name": "Vikram Reddy", "owner_email": "techzone@demo.com"},
        "products": [
            {"name": "Wireless Earbuds", "price": 1999, "cost_price": 1200, "quantity": 40},
            {"name": "Power Bank 10000mAh", "price": 999, "cost_price": 600, "quantity": 50},
            {"name": "USB-C Cable 1m", "price": 299, "cost_price": 150, "quantity": 100},
            {"name": "Phone Case Universal", "price": 399, "cost_price": 180, "quantity": 80},
            {"name": "Bluetooth Speaker", "price": 1499, "cost_price": 900, "quantity": 30},
        ]
    },
    "Sports & Fitness": {
        "shop": {"name": "FitGear Pro", "description": "Sports equipment & fitness gear", "city": "Pune", "owner_name": "Rahul Deshmukh", "owner_email": "fitgearpro@demo.com"},
        "products": [
            {"name": "Yoga Mat Premium", "price": 799, "cost_price": 450, "quantity": 40},
            {"name": "Dumbbell Set 5kg", "price": 1299, "cost_price": 800, "quantity": 25},
            {"name": "Skipping Rope", "price": 249, "cost_price": 120, "quantity": 60},
            {"name": "Resistance Bands Set", "price": 599, "cost_price": 350, "quantity": 45},
            {"name": "Cricket Ball Leather", "price": 450, "cost_price": 280, "quantity": 50},
        ]
    },
    "Home & Kitchen": {
        "shop": {"name": "Home Essentials", "description": "Everything for your home", "city": "Kolkata", "owner_name": "Anita Sen", "owner_email": "homeessentials@demo.com"},
        "products": [
            {"name": "Non-Stick Pan Set", "price": 1499, "cost_price": 900, "quantity": 20},
            {"name": "Cotton Bedsheet Double", "price": 899, "cost_price": 550, "quantity": 30},
            {"name": "Glass Water Bottle 1L", "price": 349, "cost_price": 180, "quantity": 50},
            {"name": "Kitchen Knife Set", "price": 799, "cost_price": 450, "quantity": 35},
            {"name": "Table Lamp LED", "price": 599, "cost_price": 350, "quantity": 40},
        ]
    },
    "Books & Stationery": {
        "shop": {"name": "Book World", "description": "Books and stationery supplies", "city": "Ahmedabad", "owner_name": "Meera Joshi", "owner_email": "bookworld@demo.com"},
        "products": [
            {"name": "Notebook A4 200 pages", "price": 120, "cost_price": 70, "quantity": 100},
            {"name": "Pen Set (10 pcs)", "price": 150, "cost_price": 80, "quantity": 80},
            {"name": "Hindi Novel Bestseller", "price": 299, "cost_price": 180, "quantity": 40},
            {"name": "Sketch Book A3", "price": 180, "cost_price": 100, "quantity": 60},
            {"name": "Highlighter Set (5 colors)", "price": 99, "cost_price": 50, "quantity": 90},
        ]
    },
    "Health & Wellness": {
        "shop": {"name": "Wellness Plus", "description": "Health supplements & wellness products", "city": "Jaipur", "owner_name": "Dr. Arun Gupta", "owner_email": "wellnessplus@demo.com"},
        "products": [
            {"name": "Multivitamin Tablets (60)", "price": 450, "cost_price": 280, "quantity": 50},
            {"name": "Protein Powder 500g", "price": 999, "cost_price": 650, "quantity": 30},
            {"name": "Hand Sanitizer 500ml", "price": 149, "cost_price": 80, "quantity": 100},
            {"name": "Digital Thermometer", "price": 299, "cost_price": 150, "quantity": 40},
            {"name": "First Aid Kit Basic", "price": 399, "cost_price": 220, "quantity": 35},
        ]
    },
    "Jewelry & Accessories": {
        "shop": {"name": "Jewel Box", "description": "Elegant jewelry & accessories", "city": "Lucknow", "owner_name": "Kavita Agarwal", "owner_email": "jewelbox@demo.com"},
        "products": [
            {"name": "Silver Earrings Pair", "price": 799, "cost_price": 480, "quantity": 30},
            {"name": "Gold Plated Bracelet", "price": 599, "cost_price": 350, "quantity": 40},
            {"name": "Leather Wallet Men", "price": 699, "cost_price": 400, "quantity": 35},
            {"name": "Pearl Necklace Set", "price": 1299, "cost_price": 750, "quantity": 20},
            {"name": "Sunglasses Unisex", "price": 499, "cost_price": 280, "quantity": 50},
        ]
    },
}


async def create_default_shops_and_products(db: AsyncSession):
    """Create default shops with products for each category"""
    from app.models.product import Product

    # First, get all categories
    result = await db.execute(select(ShopCategory))
    categories = {cat.name: cat.id for cat in result.scalars().all()}

    # Check if we already have shops (don't seed if data exists)
    shop_count = await db.execute(select(func.count(Shop.id)))
    if shop_count.scalar() > 0:
        print("✓ Shops already exist, skipping default shop seeding")
        return

    shops_created = 0
    products_created = 0

    for cat_name, data in DEFAULT_SHOPS_DATA.items():
        # Find matching category
        category_id = None
        for db_cat_name, cat_id in categories.items():
            if cat_name.lower() in db_cat_name.lower() or db_cat_name.lower() in cat_name.lower():
                category_id = cat_id
                break

        if not category_id:
            continue

        shop_data = data["shop"]

        # Create shop
        shop = Shop(
            name=shop_data["name"],
            description=shop_data["description"],
            city=shop_data["city"],
            owner_name=shop_data["owner_name"],
            owner_email=shop_data["owner_email"],
            category_id=category_id,
            is_verified=True,
            is_active=True,
        )
        db.add(shop)
        await db.flush()  # Get shop.id
        shops_created += 1

        # Create products for this shop
        for prod_data in data["products"]:
            product = Product(
                name=prod_data["name"],
                price=prod_data["price"],
                cost_price=prod_data["cost_price"],
                min_price=prod_data["price"] * 0.85,  # 15% min discount
                quantity=prod_data["quantity"],
                min_stock_level=10,
                shop_id=shop.id,
                is_active=True,
            )
            db.add(product)
            products_created += 1

    await db.commit()
    print(f"✓ Created {shops_created} default shops with {products_created} products")
