import time
import pdfplumber
from typing import Dict, List, Tuple
from statistics import mean, stdev
import json
from datetime import datetime
import os
from difflib import SequenceMatcher
import PIL
from tqdm import tqdm

class PDFBenchmarkSuite:
    def __init__(self, pdf_path: str, ground_truth_text: str = None):
        """
        Initialize benchmark suite
        Args:
            pdf_path: Path to PDF file
            ground_truth_text: Path to ground truth text file for quality comparison
        """
        self.pdf_path = pdf_path
        self.ground_truth_text = None
        if ground_truth_text and os.path.exists(ground_truth_text):
            with open(ground_truth_text, 'r', encoding='utf-8') as f:
                self.ground_truth_text = f.read()
        self.results = {}

    def time_operation(self, operation: callable, iterations: int = 5) -> Dict:
        """Generic timing function for operations"""
        times = []
        results = None

        for _ in range(iterations):
            start_time = time.time()
            with pdfplumber.open(self.pdf_path) as pdf:
                results = operation(pdf)
            duration = time.time() - start_time
            times.append(duration)

        return {
            "mean": mean(times),
            "std_dev": stdev(times) if len(times) > 1 else 0,
            "min": min(times),
            "max": max(times),
            "iterations": iterations,
            "raw_times": times,
            "results": results
        }

    def benchmark_text_extraction(self, iterations: int = 5) -> Dict:
        """Benchmark text extraction speed"""
        def extract_text(pdf):
            text = ""
            for page in tqdm(pdf.pages, desc="Extracting text"):
                text += page.extract_text() or ""
            return text

        print("\nBenchmarking text extraction...")
        results = self.time_operation(extract_text, iterations)
        self.results["text_extraction"] = results
        return results

    def benchmark_image_extraction(self, iterations: int = 5) -> Dict:
        """Benchmark image extraction speed"""
        def extract_images(pdf) -> List[Dict]:
            images = []
            for page_num, page in enumerate(tqdm(pdf.pages, desc="Extracting images")):
                page_images = page.images
                for img in page_images:
                    img["page_number"] = page_num + 1
                images.extend(page_images)
            return images

        print("\nBenchmarking image extraction...")
        results = self.time_operation(extract_images, iterations)
        self.results["image_extraction"] = results
        return results

    def benchmark_text_quality(self) -> Dict:
        """Benchmark text extraction quality"""
        if not self.ground_truth_text:
            print("Warning: No ground truth text provided for quality comparison")
            return None

        print("\nBenchmarking text quality...")
        with pdfplumber.open(self.pdf_path) as pdf:
            extracted_text = ""
            for page in tqdm(pdf.pages, desc="Extracting text for quality check"):
                extracted_text += page.extract_text() or ""

        # Calculate similarity ratio
        similarity = SequenceMatcher(None, self.ground_truth_text, extracted_text).ratio()

        # Calculate character accuracy
        total_chars = len(self.ground_truth_text)
        char_diff = abs(len(extracted_text) - total_chars)
        char_accuracy = 1 - (char_diff / total_chars)

        results = {
            "similarity_ratio": similarity,
            "character_accuracy": char_accuracy,
            "extracted_length": len(extracted_text),
            "ground_truth_length": len(self.ground_truth_text)
        }

        self.results["text_quality"] = results
        return results

    def run_all_benchmarks(self, iterations: int = 5):
        """Run all benchmarks"""
        self.benchmark_text_extraction(iterations)
        self.benchmark_image_extraction(iterations)
        self.benchmark_text_quality()

    def save_results(self, filename: str = None):
        """Save benchmark results to JSON"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pdf_benchmark_results_{timestamp}.json"

        # Convert any non-serializable objects to strings
        serializable_results = json.loads(
            json.dumps(self.results, default=str)
        )

        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=4)
        print(f"\nResults saved to {filename}")

    def print_summary(self):
        """Print benchmark summary"""
        print("\nBenchmark Summary:")
        print("=" * 50)

        # Speed benchmarks
        for benchmark in ["text_extraction", "image_extraction"]:
            if benchmark in self.results:
                res = self.results[benchmark]
                print(f"\n{benchmark.replace('_', ' ').title()}:")
                print(f"  Average time: {res['mean']:.3f} sec")
                print(f"  Std Dev: {res['std_dev']:.3f} sec")
                print(f"  Min time: {res['min']:.3f} sec")
                print(f"  Max time: {res['max']:.3f} sec")

        # Quality benchmark
        if "text_quality" in self.results:
            print("\nText Quality Metrics:")
            quality = self.results["text_quality"]
            print(f"  Similarity ratio: {quality['similarity_ratio']:.3f}")
            print(f"  Character accuracy: {quality['character_accuracy']:.3f}")

def main():
    # pdf_path = "2201.00214v1.pdf"
    # ground_truth_path = "./ground-truth/2201.00214.txt"  # Optional

    pdf_path = "GeoTopo.pdf"
    ground_truth_path = "./ground-truth/GeoTopo-book.txt"  # Optional

    benchmark = PDFBenchmarkSuite(
        pdf_path=pdf_path,
        ground_truth_text=ground_truth_path
    )

    benchmark.run_all_benchmarks(iterations=3)

    benchmark.print_summary()
    benchmark.save_results()

if __name__ == "__main__":
    main()
