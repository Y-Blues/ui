# ycappuccino-ui

Une bibliothèque de description d'écran, pas un toolkit graphique : un `Screen` décrit un formulaire
(champs + actions) une seule fois — normalement chargé depuis un template YAML/JSON, jamais construit à
la main pour chaque écran — sans savoir s'il sera rendu en shell, en Qt ou dans un navigateur. Le rendu est
le rôle des adapters séparés (`ycappuccino-ui-shell` pour le terminal, à venir : `ycappuccino-ui-qt`,
`ycappuccino-ui-web` en HTML/CSS/pyscript). Une `Action` ne porte jamais de callable Python écrit à la
main : elle nomme un `Endpoint` (service/méthode/chemin), appelé génériquement par
`ycappuccino.ui.transport.perform_action` — la bibliothèque Python se limite au chargement du template et
au câblage générique des événements, jamais à la logique d'un écran particulier.

Conception : [docs/superpowers/specs/2026-09-16-ui-screen-library-checkpoint.md](../remote/docs/superpowers/specs/2026-09-16-ui-screen-library-checkpoint.md)
(brainstorming en cours, pas une spec figée — vit provisoirement dans `remote/docs/` faute d'un meilleur
endroit).

Aucune dépendance à `ycappuccino.api`/`ycappuccino.core` : `Screen`/`Field`/`Action`/`Endpoint` sont de
simples `dataclasses`, testables sans aucun toolkit de rendu installé et sans le reste du framework — un
choix délibéré, plus léger que de réutiliser le mécanisme `@Item`/`@Property` de
`ycappuccino.api.decorators` (pensé pour des modèles persistés via `IManager`, ce qu'un écran n'est pas).
`Endpoint(service, method, path, params)` reprend volontairement la même forme d'adressage que
`IExposedService.call(method, extra_path, params, body, subject)` (`ycappuccino.api.endpoints_service`,
déjà utilisée par `remote`) plutôt que d'en inventer une seconde.

## Décrire un écran en YAML

```yaml
title: Connexion
fields:
  - name: username
    label: Nom d'utilisateur
    required: true
actions:
  - name: submit
    label: Se connecter
    endpoint:
      service: login
      method: POST
```

```python
from ycappuccino.ui.loader import load_screen_yaml

screen = load_screen_yaml(open("screen.yml").read())
```

`load_screen_json` fait la même chose pour du JSON, `load_screen(data)` accepte un `dict` déjà parsé.

Types de champ disponibles (`Field.type`) : `"text"` (défaut), `"number"`, `"boolean"`, `"choice"`
(nécessite `choices: [...]`, non vide), `"date"`.

## `$template` : le service décrit son propre écran

Inspiré de [SData 2.0](https://sage.github.io/SData-2.0/) (`entity/$template` renvoie une instance par
défaut d'une ressource, `entity/$schema` la décrit) : un backend peut décrire lui-même son écran plutôt que
chaque client n'en réécrive un. `fetch_screen(transport, service)` appelle
`service/$template` via le `Transport` générique (voir plus bas) et parse la réponse comme n'importe quel
template YAML/JSON chargé localement — seule l'idée est reprise de SData, pas son format de payload
Atom/XML.

## Décrire un écran directement en Python

Équivalent, sans passer par un fichier — utile pour les tests, ou un écran généré dynamiquement :

```python
from ycappuccino.ui.model import Action, Endpoint, Field, Screen

screen = Screen(
    title="Connexion",
    fields=(
        Field(name="username", label="Nom d'utilisateur", required=True),
        Field(name="remember_me", label="Se souvenir de moi", type="boolean", default=False),
    ),
    actions=(Action(name="submit", label="Se connecter", endpoint=Endpoint(service="login")),),
)
```

## Valider

`validate_screen(screen, values)` applique `required` et l'éventuel `Field.validate` (un callable Python
`valeur -> message d'erreur ou None`, donc uniquement disponible sur un écran construit en Python, pas
chargé depuis un template — un échappatoire pour de la validation avancée, pas le cas courant) — la même
logique pour tous les adapters, jamais réimplémentée par renderer :

```python
from ycappuccino.ui.validation import validate_screen

errors = validate_screen(screen, {"username": ""})
# {"username": "Nom d'utilisateur is required"}
```

`Field.validate` n'est appelé que si le champ n'est pas vide (`required` couvre déjà le cas vide) —
`Field.default` sert de valeur de repli si la clé est absente de `values`.

## Appeler l'action d'un écran

`perform_action(action, values, transport)` est le dispatch générique que tout adapter réutilise : il
construit le corps de la requête (`Endpoint.params` puis les valeurs de champs par-dessus) et appelle
`transport.call(service, method, path, params, body)`. `Transport` est un `Protocol` — chaque déploiement
fournit le sien (HTTP direct, `ycappuccino-client`'s `HttpTransport` dans un navigateur, un
`IServiceEndpoint` local si l'adapter tourne dans le même process que le backend) :

```python
import asyncio

from ycappuccino.ui.transport import perform_action


class ExampleTransport:
    async def call(self, service, method, path, params, body):
        return {"received": {"service": service, "method": method, "path": path, "body": body}}


async def main():
    result = await perform_action(screen.actions[0], {"username": "aurelien"}, ExampleTransport())
    return result
```

## Développer ui

```bash
uv sync
uv run python -m unittest discover -s src/unittest/python
```
