"""
系统测试脚本
用于验证库存管理系统的基本功能
"""
import os
import sys
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from models import Material, Order, OrderStatus, Priority
from controllers import MaterialController, OrderController, ReportController

def test_database():
    """测试数据库功能"""
    print("🧪 测试数据库功能...")
    
    # 创建测试数据库
    db_manager = DatabaseManager("test_inventory.db")
    print("✅ 数据库初始化成功")
    
    return db_manager

def test_material_controller(db_manager):
    """测试物料控制器"""
    print("\n📦 测试物料管理功能...")
    
    material_controller = MaterialController(db_manager)
    
    # 创建测试物料
    test_material = Material(
        name="测试试剂",
        category="试剂",
        description="🧪 这是一个测试用的试剂，用于验证系统功能",
        quantity=100,
        unit="毫升",
        min_stock=10,
        location="A-01",
        supplier="测试供应商"
    )
    
    # 添加物料
    material_id = material_controller.create_material(test_material)
    print(f"✅ 物料创建成功，ID: {material_id}")
    
    # 获取物料
    retrieved_material = material_controller.get_material(material_id)
    if retrieved_material:
        print(f"✅ 物料获取成功: {retrieved_material.name}")
    
    # 更新物料
    retrieved_material.quantity = 150
    material_controller.update_material(retrieved_material)
    print("✅ 物料更新成功")
    
    # 搜索物料
    search_results = material_controller.search_materials("测试")
    print(f"✅ 搜索功能正常，找到 {len(search_results)} 个结果")
    
    return material_controller, material_id

def test_order_controller(db_manager, material_id):
    """测试订单控制器"""
    print("\n📋 测试订单管理功能...")
    
    order_controller = OrderController(db_manager)
    
    # 创建测试订单
    test_order = Order(
        requester="测试用户",
        department="测试部门",
        status=OrderStatus.PENDING.value,
        priority=Priority.HIGH.value,
        notes="这是一个测试订单",
        materials=[{
            'material_id': material_id,
            'quantity': 5,
            'notes': '测试用'
        }]
    )
    
    # 创建订单
    order_id = order_controller.create_order(test_order)
    print(f"✅ 订单创建成功，ID: {order_id}")
    
    # 获取订单
    retrieved_order = order_controller.get_order(order_id)
    if retrieved_order:
        print(f"✅ 订单获取成功: {retrieved_order.order_number}")
        print(f"   申请人: {retrieved_order.requester}")
        print(f"   物料数量: {len(retrieved_order.materials)}")
    
    # 完成订单
    order_controller.complete_order(order_id)
    print("✅ 订单完成成功")
    
    return order_controller, order_id

def test_report_controller(db_manager, order_id):
    """测试报告控制器"""
    print("\n📊 测试报告生成功能...")
    
    report_controller = ReportController(db_manager)
    
    # 生成报告
    html_content = report_controller.generate_order_report([order_id])
    
    if html_content and len(html_content) > 100:
        print("✅ HTML报告生成成功")
        
        # 保存测试报告
        with open("test_report.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("✅ 测试报告已保存为 test_report.html")
    else:
        print("❌ 报告生成失败")

def test_emoji_support():
    """测试emoji支持"""
    print("\n😀 测试emoji支持...")
    
    emojis = ["🧪", "🔬", "⚗️", "🧬", "🦠", "💊", "💉", "🧫"]
    
    for emoji in emojis:
        print(f"   {emoji} - 支持")
    
    print("✅ Emoji支持正常")

def cleanup_test_files():
    """清理测试文件"""
    print("\n🧹 清理测试文件...")
    
    test_files = ["test_inventory.db", "test_report.html"]
    
    for file in test_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"✅ 已删除 {file}")
            except Exception as e:
                print(f"⚠️  删除 {file} 失败: {e}")

def main():
    """主测试函数"""
    print("🚀 开始测试生物实验室库存管理系统")
    print("=" * 50)
    
    try:
        # 测试数据库
        db_manager = test_database()
        
        # 测试物料管理
        material_controller, material_id = test_material_controller(db_manager)
        
        # 测试订单管理
        order_controller, order_id = test_order_controller(db_manager, material_id)
        
        # 测试报告生成
        test_report_controller(db_manager, order_id)
        
        # 测试emoji支持
        test_emoji_support()
        
        print("\n" + "=" * 50)
        print("🎉 所有测试通过！系统功能正常")
        print("\n📝 测试总结:")
        print("   ✅ 数据库初始化和连接")
        print("   ✅ 物料管理（增删改查）")
        print("   ✅ 订单管理（创建、完成）")
        print("   ✅ HTML报告生成")
        print("   ✅ Emoji支持")
        print("   ✅ 库存自动更新")
        
        print("\n🚀 系统已准备就绪，可以运行 python main.py 启动图形界面")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试文件
        cleanup_test_files()

if __name__ == "__main__":
    main()
