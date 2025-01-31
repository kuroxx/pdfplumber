import time
import pdfplumber

def benchmark_extraction(pdf_path, num_iterations=5):
    times = []
    
    for _ in range(num_iterations):
        start_time = time.time()
        
        with pdfplumber.open(pdf_path) as pdf:
            print('extracting text from all pages...')
            text = ''
            for page in pdf.pages:
                text += page.extract_text()
                
        end_time = time.time()

        diff = end_time - start_time
        times.append(diff)
        print(f'{diff} sec')
    
    avg_time = sum(times) / len(times)
    return avg_time

time = benchmark_extraction('2201.00214v1.pdf', 2)

print(f'average time {time} sec')