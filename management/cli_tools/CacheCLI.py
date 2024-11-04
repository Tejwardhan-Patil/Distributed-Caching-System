import argparse
import sys
import json
import requests

class CacheCLI:
    def __init__(self):
        self.base_url = "http://localhost:8080/cache"
        self.parser = argparse.ArgumentParser(
            description="CLI tool for interacting with the Distributed Cache System"
        )
        self._init_arguments()
    
    def _init_arguments(self):
        subparsers = self.parser.add_subparsers(dest='command', help='Cache operations')

        # Set command
        set_parser = subparsers.add_parser('set', help='Set a value in the cache')
        set_parser.add_argument('key', type=str, help='Cache key')
        set_parser.add_argument('value', type=str, help='Cache value')

        # Get command
        get_parser = subparsers.add_parser('get', help='Get a value from the cache')
        get_parser.add_argument('key', type=str, help='Cache key')

        # Delete command
        del_parser = subparsers.add_parser('delete', help='Delete a value from the cache')
        del_parser.add_argument('key', type=str, help='Cache key')

        # List command
        list_parser = subparsers.add_parser('list', help='List all cache keys')

        # Clear command
        clear_parser = subparsers.add_parser('clear', help='Clear all cache entries')

        # Cache stats
        stats_parser = subparsers.add_parser('stats', help='Display cache statistics')

    def execute(self):
        args = self.parser.parse_args()
        if not args.command:
            self.parser.print_help()
            sys.exit(1)
        
        if args.command == 'set':
            self.set_cache(args.key, args.value)
        elif args.command == 'get':
            self.get_cache(args.key)
        elif args.command == 'delete':
            self.delete_cache(args.key)
        elif args.command == 'list':
            self.list_cache()
        elif args.command == 'clear':
            self.clear_cache()
        elif args.command == 'stats':
            self.cache_stats()
    
    def set_cache(self, key, value):
        try:
            response = requests.post(f"{self.base_url}/set", json={"key": key, "value": value})
            if response.status_code == 200:
                print(f"Successfully set key '{key}' with value '{value}'")
            else:
                print(f"Failed to set key '{key}': {response.text}")
        except Exception as e:
            print(f"Error setting cache: {str(e)}")
    
    def get_cache(self, key):
        try:
            response = requests.get(f"{self.base_url}/get/{key}")
            if response.status_code == 200:
                value = response.json().get("value")
                print(f"Key '{key}' has value: '{value}'")
            elif response.status_code == 404:
                print(f"Key '{key}' not found in cache.")
            else:
                print(f"Failed to get key '{key}': {response.text}")
        except Exception as e:
            print(f"Error getting cache: {str(e)}")
    
    def delete_cache(self, key):
        try:
            response = requests.delete(f"{self.base_url}/delete/{key}")
            if response.status_code == 200:
                print(f"Successfully deleted key '{key}'")
            else:
                print(f"Failed to delete key '{key}': {response.text}")
        except Exception as e:
            print(f"Error deleting cache: {str(e)}")
    
    def list_cache(self):
        try:
            response = requests.get(f"{self.base_url}/list")
            if response.status_code == 200:
                keys = response.json().get("keys", [])
                if keys:
                    print("Cache keys:")
                    for key in keys:
                        print(f" - {key}")
                else:
                    print("Cache is empty.")
            else:
                print(f"Failed to list cache keys: {response.text}")
        except Exception as e:
            print(f"Error listing cache: {str(e)}")
    
    def clear_cache(self):
        try:
            response = requests.post(f"{self.base_url}/clear")
            if response.status_code == 200:
                print("Successfully cleared the cache")
            else:
                print(f"Failed to clear the cache: {response.text}")
        except Exception as e:
            print(f"Error clearing cache: {str(e)}")
    
    def cache_stats(self):
        try:
            response = requests.get(f"{self.base_url}/stats")
            if response.status_code == 200:
                stats = response.json()
                print("Cache statistics:")
                print(json.dumps(stats, indent=4))
            else:
                print(f"Failed to retrieve cache statistics: {response.text}")
        except Exception as e:
            print(f"Error fetching cache statistics: {str(e)}")


def main():
    cli = CacheCLI()
    cli.execute()


if __name__ == "__main__":
    main()