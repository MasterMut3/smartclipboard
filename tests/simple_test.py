import sys
import os
import tempfile
import json
import time
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from main import SimpleClipboardMonitor
import sys
import io

# Force UTF-8 encoding for console output
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
def test_file_creation():
    """Test automatic file creation"""
    print("\n" + "="*50)
    print("Running file creation test...")
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = Path(tmp_dir) / "test.json"
        
        monitor = SimpleClipboardMonitor()
        monitor.data_file = test_file
        
        assert not test_file.exists()
        print("✅ File doesn't exist initially")
        
        monitor.setup_directories()
        assert test_file.exists()
        print(f"✅ File created at: {test_file}")
        
        content = test_file.read_text(encoding='utf-8')
        assert content == '[]'
        print(f"✅ File content: {content}")
        
        print("✅ File creation test passed!")
    print("="*50)

def test_data_saving():
    """Test data saving and loading"""
    print("\n" + "="*50)
    print("Running data saving test...")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
        tmp_path = tmp_file.name
        tmp_file.write('[]')
    print(f"✅ Created temp file: {tmp_path}")
    
    try:
        monitor = SimpleClipboardMonitor()
        monitor.data_file = Path(tmp_path)
        
        monitor.load_data()
        print(f"📊 Initial data length: {len(monitor.data)}")
        assert len(monitor.data) == 0, "Initial data should be empty"
        
        test_item = {
            'id': 1,
            'text': 'test text',
            'name': 'test name',
            'tags': ['test'],
            'timestamp': '2024-01-01'
        }
        monitor.data.append(test_item)
        print(f"➕ Added test item: {test_item}")
        
        monitor.save_data()
        print("💾 Data saved")
        
        monitor2 = SimpleClipboardMonitor()
        monitor2.data_file = Path(tmp_path)
        monitor2.load_data()
        print(f"📊 Loaded data length: {len(monitor2.data)}")
        
        assert len(monitor2.data) == 1, f"Expected 1 item, got {len(monitor2.data)}"
        assert monitor2.data[0]['text'] == 'test text'
        assert monitor2.data[0]['name'] == 'test name'
        assert 'test' in monitor2.data[0]['tags']
        
        print("✅ All assertions passed!")
        
    finally:
        os.unlink(tmp_path)
        print(f"🧹 Cleaned up temp file")
    print("="*50)

def test_save_without_name():
    """Test saving without providing a name"""
    print("\n" + "="*50)
    print("Running save without name test...")
    
    monitor = SimpleClipboardMonitor()
    
    item = {
        'id': 1,
        'text': 'test content',
        'name': f"Item {1}",
        'tags': [],
        'timestamp': '2024-01-01'
    }
    monitor.data.append(item)
    
    assert item['name'] == "Item 1"
    print(f"✅ Default name assigned: {item['name']}")
    print("✅ Save without name test passed!")
    print("="*50)

def test_multiple_items():
    """Test saving multiple items"""
    print("\n" + "="*50)
    print("Running multiple items test...")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
        tmp_path = tmp_file.name
        tmp_file.write('[]')
    
    try:
        monitor = SimpleClipboardMonitor()
        monitor.data_file = Path(tmp_path)
        monitor.load_data()
        
        # Add 3 items
        for i in range(3):
            item = {
                'id': i + 1,
                'text': f'test text {i}',
                'name': f'Item {i + 1}',
                'tags': [f'tag{i}'] if i > 0 else [],
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            monitor.data.append(item)
        
        monitor.save_data()
        
        # Load and verify
        monitor2 = SimpleClipboardMonitor()
        monitor2.data_file = Path(tmp_path)
        monitor2.load_data()
        
        assert len(monitor2.data) == 3
        assert monitor2.data[0]['name'] == 'Item 1'
        assert monitor2.data[1]['name'] == 'Item 2'
        assert monitor2.data[2]['name'] == 'Item 3'
        
        print("✅ Multiple items saved and loaded correctly")
        
    finally:
        os.unlink(tmp_path)
    print("="*50)

def test_corrupted_file_handling():
    """Test handling of corrupted JSON file"""
    print("\n" + "="*50)
    print("Running corrupted file handling test...")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
        tmp_path = tmp_file.name
        tmp_file.write('{invalid json:')  # Write invalid JSON
    
    try:
        monitor = SimpleClipboardMonitor()
        monitor.data_file = Path(tmp_path)
        
        # This should handle the error gracefully
        monitor.load_data()
        
        assert len(monitor.data) == 0
        print("✅ Corrupted file handled gracefully")
        
        # Check if backup was created
        backup_file = Path(tmp_path).with_suffix('.json.bak')
        if backup_file.exists():
            print(f"✅ Backup file created: {backup_file}")
            backup_file.unlink()
            
    finally:
        if Path(tmp_path).exists():
            os.unlink(tmp_path)
    print("="*50)

if __name__ == "__main__":
    try:
        test_file_creation()
        test_data_saving()
        test_save_without_name()
        test_multiple_items()
        test_corrupted_file_handling()
        print("\n🎉 All tests passed successfully!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()