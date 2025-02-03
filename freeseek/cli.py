import click

@click.group()
def cli():
    pass

@cli.command()
@click.option('--api-key', prompt='Your API Key', help='Your Freeseek API Key')
def configure(api_key: str):
    # Simulate configuration logic.
    print(f"Configured with API Key: {api_key}")

if __name__ == '__main__':
    cli()