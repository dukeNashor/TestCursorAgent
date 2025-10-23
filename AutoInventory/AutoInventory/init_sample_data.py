"""
示例数据初始化脚本
为系统添加一些示例数据，方便用户快速开始使用
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from models import Material, Order, OrderStatus, Priority
from controllers import MaterialController, OrderController

def init_sample_materials(material_controller):
    """初始化示例物料数据"""
    print("📦 初始化示例物料数据...")
    
    sample_materials = [
        Material(
            name="PBS缓冲液",
            category="试剂",
            description="🧪 磷酸盐缓冲液，用于细胞培养和实验",
            quantity=50,
            unit="升",
            min_stock=5,
            location="A-01",
            supplier="生物试剂公司"
        ),
        Material(
            name="移液器吸头",
            category="耗材",
            description="🔬 200μL移液器吸头，无菌包装",
            quantity=1000,
            unit="盒",
            min_stock=50,
            location="B-02",
            supplier="实验耗材供应商"
        ),
        Material(
            name="细胞培养皿",
            category="耗材",
            description="🧫 35mm细胞培养皿，用于细胞培养实验",
            quantity=200,
            unit="个",
            min_stock=20,
            location="B-03",
            supplier="细胞培养用品公司"
        ),
        Material(
            name="DNA提取试剂盒",
            category="试剂",
            description="🧬 快速DNA提取试剂盒，适用于多种样本类型",
            quantity=30,
            unit="盒",
            min_stock=5,
            location="A-02",
            supplier="分子生物学公司"
        ),
        Material(
            name="PCR管",
            category="耗材",
            description="⚗️ 0.2mL PCR管，适用于PCR反应",
            quantity=500,
            unit="盒",
            min_stock=20,
            location="B-04",
            supplier="PCR用品供应商"
        ),
        Material(
            name="显微镜载玻片",
            category="耗材",
            description="🔍 标准显微镜载玻片，用于样本观察",
            quantity=300,
            unit="盒",
            min_stock=10,
            location="C-01",
            supplier="光学仪器公司"
        ),
        Material(
            name="胰蛋白酶",
            category="试剂",
            description="💊 细胞消化用胰蛋白酶，0.25%浓度",
            quantity=20,
            unit="瓶",
            min_stock=3,
            location="A-03",
            supplier="细胞培养试剂公司"
        ),
        Material(
            name="离心管",
            category="耗材",
            description="⚗️ 15mL离心管，用于样本离心",
            quantity=400,
            unit="盒",
            min_stock=20,
            location="B-05",
            supplier="实验耗材供应商"
        ),
        Material(
            name="琼脂糖",
            category="试剂",
            description="🧪 电泳用琼脂糖，用于DNA电泳",
            quantity=10,
            unit="克",
            min_stock=2,
            location="A-04",
            supplier="分子生物学公司"
        ),
        Material(
            name="手套",
            category="耗材",
            description="🧤 一次性实验手套，无菌包装",
            quantity=100,
            unit="盒",
            min_stock=10,
            location="D-01",
            supplier="防护用品公司"
        )
    ]
    
    created_materials = []
    for material in sample_materials:
        try:
            material_id = material_controller.create_material(material)
            created_materials.append(material_id)
            print(f"   ✅ {material.name} - 已添加")
        except Exception as e:
            print(f"   ❌ {material.name} - 添加失败: {e}")
    
    print(f"📦 成功添加 {len(created_materials)} 个示例物料")
    return created_materials

def init_sample_orders(order_controller, material_ids):
    """初始化示例订单数据"""
    print("\n📋 初始化示例订单数据...")
    
    if len(material_ids) < 3:
        print("⚠️  物料数量不足，跳过订单初始化")
        return []
    
    sample_orders = [
        Order(
            requester="张研究员",
            department="分子生物学实验室",
            status=OrderStatus.PENDING.value,
            priority=Priority.HIGH.value,
            notes="急需用于DNA提取实验",
            materials=[
                {
                    'material_id': material_ids[3],  # DNA提取试剂盒
                    'quantity': 2,
                    'notes': '用于血液样本DNA提取'
                },
                {
                    'material_id': material_ids[4],  # PCR管
                    'quantity': 1,
                    'notes': 'PCR反应用'
                }
            ]
        ),
        Order(
            requester="李博士",
            department="细胞生物学实验室",
            status=OrderStatus.IN_PROGRESS.value,
            priority=Priority.NORMAL.value,
            notes="细胞培养实验用",
            materials=[
                {
                    'material_id': material_ids[0],  # PBS缓冲液
                    'quantity': 5,
                    'notes': '细胞洗涤用'
                },
                {
                    'material_id': material_ids[2],  # 细胞培养皿
                    'quantity': 20,
                    'notes': '细胞培养用'
                },
                {
                    'material_id': material_ids[6],  # 胰蛋白酶
                    'quantity': 1,
                    'notes': '细胞消化用'
                }
            ]
        ),
        Order(
            requester="王技术员",
            department="病理学实验室",
            status=OrderStatus.COMPLETED.value,
            priority=Priority.LOW.value,
            notes="常规实验用品补充",
            materials=[
                {
                    'material_id': material_ids[1],  # 移液器吸头
                    'quantity': 2,
                    'notes': '日常实验用'
                },
                {
                    'material_id': material_ids[5],  # 显微镜载玻片
                    'quantity': 1,
                    'notes': '样本观察用'
                },
                {
                    'material_id': material_ids[9],  # 手套
                    'quantity': 1,
                    'notes': '防护用品'
                }
            ]
        )
    ]
    
    created_orders = []
    for order in sample_orders:
        try:
            order_id = order_controller.create_order(order)
            created_orders.append(order_id)
            print(f"   ✅ 订单 {order.requester} - 已创建")
            
            # 如果是已完成的订单，标记为完成
            if order.status == OrderStatus.COMPLETED.value:
                order_controller.complete_order(order_id)
                print(f"      ✅ 订单已完成")
                
        except Exception as e:
            print(f"   ❌ 订单 {order.requester} - 创建失败: {e}")
    
    print(f"📋 成功创建 {len(created_orders)} 个示例订单")
    return created_orders

def main():
    """主函数"""
    print("🚀 初始化生物实验室库存管理系统示例数据")
    print("=" * 50)
    
    try:
        # 初始化数据库
        db_manager = DatabaseManager()
        material_controller = MaterialController(db_manager)
        order_controller = OrderController(db_manager)
        
        # 检查是否已有数据
        existing_materials = material_controller.get_all_materials()
        if existing_materials:
            print(f"⚠️  系统中已有 {len(existing_materials)} 个物料")
            response = input("是否要添加示例数据？(y/n): ").lower().strip()
            if response != 'y':
                print("取消初始化")
                return
        
        # 初始化示例物料
        material_ids = init_sample_materials(material_controller)
        
        # 初始化示例订单
        order_ids = init_sample_orders(order_controller, material_ids)
        
        print("\n" + "=" * 50)
        print("🎉 示例数据初始化完成！")
        print(f"📦 物料数量: {len(material_ids)}")
        print(f"📋 订单数量: {len(order_ids)}")
        print("\n🚀 现在可以运行 python main.py 启动系统")
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
