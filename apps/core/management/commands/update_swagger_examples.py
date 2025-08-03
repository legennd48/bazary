"""
Management command to update Swagger documentation with captured responses.
"""

import json

from django.core.management.base import BaseCommand

from apps.core.response_capture import response_capture


class Command(BaseCommand):
    help = "Update Swagger documentation with captured API responses"

    def add_arguments(self, parser):
        parser.add_argument(
            "--endpoint", type=str, help="Update examples for specific endpoint only"
        )
        parser.add_argument(
            "--clear", action="store_true", help="Clear all captured examples"
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.clear_examples()
            return

        endpoint = options.get("endpoint")
        examples = response_capture.load_examples_for_swagger()

        if not examples:
            self.stdout.write(
                self.style.WARNING(
                    "No captured examples found. Make some API calls first."
                )
            )
            return

        if endpoint:
            if endpoint in examples:
                self.update_single_endpoint(endpoint, examples[endpoint])
            else:
                self.stdout.write(
                    self.style.ERROR(f"No examples found for endpoint: {endpoint}")
                )
        else:
            self.update_all_endpoints(examples)

    def update_single_endpoint(self, endpoint_name, endpoint_examples):
        """Update examples for a single endpoint."""
        self.stdout.write(f"Updating examples for {endpoint_name}...")

        for method, method_examples in endpoint_examples.items():
            for status_code, example in method_examples.items():
                self.stdout.write(
                    f'  {method} {status_code}: {len(str(example["value"]))} chars'
                )

        self.stdout.write(self.style.SUCCESS(f"Updated {endpoint_name} examples"))

    def update_all_endpoints(self, examples):
        """Update examples for all endpoints."""
        self.stdout.write("Updating all Swagger examples...")

        total_examples = 0
        for endpoint_name, endpoint_examples in examples.items():
            self.stdout.write(f"\n📡 {endpoint_name}:")

            for method, method_examples in endpoint_examples.items():
                for status_code, example in method_examples.items():
                    total_examples += 1
                    timestamp = example.get("description", "").replace(
                        "Captured response from ", ""
                    )
                    self.stdout.write(f"  ✅ {method} {status_code} - {timestamp[:19]}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎉 Updated {total_examples} examples across {len(examples)} endpoints"
            )
        )

        # Show next steps
        self.stdout.write("\n📝 Next steps:")
        self.stdout.write("1. Review captured examples in swagger_examples/ directory")
        self.stdout.write("2. Update your view decorators to use captured examples")
        self.stdout.write("3. Restart your server to see updated Swagger docs")

    def clear_examples(self):
        """Clear all captured examples."""
        examples_dir = response_capture.examples_dir

        if not examples_dir.exists():
            self.stdout.write("No examples directory found.")
            return

        example_files = list(examples_dir.glob("*.json"))

        if not example_files:
            self.stdout.write("No examples to clear.")
            return

        for file_path in example_files:
            file_path.unlink()

        self.stdout.write(
            self.style.SUCCESS(f"Cleared {len(example_files)} example files")
        )
