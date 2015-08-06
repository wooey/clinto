import click

@click.command()
def hello():
    click.echo('Hello World!')

@click.command()
@click.option('--count', default=1, help='number of greetings')
@click.argument('name')
def hello2(count, name):
    for x in range(count):
        click.echo('Hello %s!' % name)