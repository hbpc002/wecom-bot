import os
import logging
from report_generator import ReportGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)

def verify_fonts():
    print("Starting font verification...")
    
    # Dummy report data
    report_data = {
        ('TeamA', 'UserA', 'AccountA'): 10,
        ('TeamB', 'UserB', 'AccountB'): 5
    }
    
    from datetime import datetime
    report_date = datetime.now()
    total_operations = 15
    filename = "test_report"
    file_dir = os.getcwd()
    
    # Generate report
    print("Generating report...")
    try:
        result = ReportGenerator.generate_report(
            report_data, 
            report_date, 
            total_operations, 
            filename, 
            file_dir, 
            output_format='image'
        )
        
        if result and result.get('filename'):
            print(f"Report generated successfully: {result['filename']}")
            print("Please check the generated image for correct font rendering (Chinese + Emoji).")
        else:
            print("Failed to generate report.")
            
    except Exception as e:
        print(f"Error during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_fonts()
