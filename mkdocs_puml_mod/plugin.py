import typing
import re

from mkdocs.config.config_options import Type, Config
from mkdocs.plugins import BasePlugin

from mkdocs_puml_mod.puml import PlantUML
from bs4 import BeautifulSoup

SUPERFENCES_EXTENSION = 'pymdownx.superfences'
CUSTOM_FENCE_FN = 'fence_puml' 

class PlantUMLPlugin(BasePlugin):
    """MKDocs plugin that converts puml diagrams into SVG images.

    It works only with a remote PlantUML service. You should add
    these configs into ``mkdocs.yml``::

            plugins:
                - mkdocs_puml:
                    puml_url: https://www.plantuml.com/plantuml
                    num_workers: 10

    Attributes:
        div_class_name (str): the class that will be set to resulting <div> tag
                              containing the diagram
        pre_class_name (str): the class that will be set to intermediate <pre> 
                              tag containing uuid code
        config_scheme (str): config scheme to set by user in mkdocs.yml file

        regex (re.Pattern): regex to find all puml code blocks
        uuid_regex (re.Pattern): regex to find all uuid <pre> blocks
        puml (PlantUML): PlantUML instance that requests PlantUML service
        diagrams (dict): Dictionary containing the diagrams (puml and later svg)
                         and their keys
        puml_keyword (str): keyword used to find PlantUML blocks within 
                            Markdown files
    """
    div_class_name = "puml"
    pre_class_name = "diagram-uuid"

    config_scheme = (
        ('puml_url', Type(str, required=True)),
        ('num_workers', Type(int, default=8)),
        ('puml_keyword', Type(str, default='puml'))
    )

    def __init__(self):
        self.regex: typing.Optional[typing.Any] = None
        self.uuid_regex = re.compile(
                rf'<pre class="{self.pre_class_name}">(.+?)</pre>', 
                flags=re.DOTALL
            )

        self.puml: typing.Optional[PlantUML] = None
        self.diagrams = {
            # key - uuid: value - puml. After on_env — svg
        }

    def on_config(self, config: Config) -> Config:
        """Event that is fired by mkdocs when configs are created.

        self.puml instance is populated in this event.

        Args:
            config: Full mkdocs.yml config file. To access configs of 
                    PlantUMLPlugin only, use self.config attribute.

        Returns:
            Full config of the mkdocs
        """
        self.puml = PlantUML(self.config['puml_url'], 
                            num_workers=self.config['num_workers'])
        self.puml_keyword = self.config['puml_keyword']
        self.regex = re.compile(rf"<pre class={self.puml_keyword}>(.+?)</pre>",
                flags=re.DOTALL)
        return config

    def on_post_page(self, output: str, *args, **kwargs) -> str:
        """The event is fired after HTML page is rendered.
        Here, we substitute <pre> tags with uuid codes of diagrams
        with the corresponding SVG images.

        Args:
            output: rendered HTML page

        Returns:
            HTML page containing SVG diagrams
        """
        if "puml" not in output:
            # Skip unecessary HTML parsing
            return output
        soup = BeautifulSoup(output, 'html.parser')

        pre_code_tags = (soup.select("pre code.puml") or 
                        soup.select("pre code.language-puml") or
                         soup.select("pre.puml code"))
        no_found = len(pre_code_tags)
        if no_found:
            puml_diags = []
            for tag in pre_code_tags:
                content = tag.text
                new_tag = soup.new_tag("div", attrs={"class": "puml"})
                #new_tag.append(content)
                puml_diags.append(content)
                # replace the parent:
                tag.parent.replaceWith(new_tag)
            # Count the diagrams <div class = 'mermaid'> ... </div>
            #puml_diags = [tag.text for tag in soup.select("div.puml")]

            resp = self.puml.translate(puml_diags)
            for tag,svg in zip(soup.select("div.puml"),resp):
                #tag.string.replace_with(BeautifulSoup(svg, 'html.parser'))
                tag.append(BeautifulSoup(svg, 'html.parser'))
        return str(soup)
