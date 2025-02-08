import os
import click
import configparser

CONFIG_FILE = os.path.expanduser("~/freeseek/config")

@click.group()
def cli():
    pass

@cli.command()
@click.option('--api-key', prompt='Your API Key', help='Your Freeseek API Key')
def configure(api_key: str):
    """Store the API key persistently."""
    config = configparser.ConfigParser()
    config["DEFAULT"] = {"API_KEY": api_key}

    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)

    click.echo("API Key saved successfully!")

@cli.command()
def show_config():
    """Display the saved API key."""
    if not os.path.exists(CONFIG_FILE):
        click.echo("No configuration found. Run `configure` first.")
        return

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    api_key = config["DEFAULT"].get("API_KEY", "Not set")
    
    click.echo(f"Stored API Key: {api_key}")

if __name__ == '__main__':
    cli()
