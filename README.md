# ycappuccino-ui

Une bibliothèque de description d'écran, pas un toolkit graphique : un `Screen` décrit un formulaire
(champs + actions) une seule fois — normalement chargé depuis un template YAML/JSON, jamais construit à
la main pour chaque écran — sans savoir s'il sera rendu en shell, en Qt ou dans un navigateur. Le rendu est
le rôle des adapters séparés (`ycappuccino-ui-shell` pour le terminal, [`ycappuccino-ui-web`](../ui_web/README.md)
pour le navigateur via Pyodide/`client`, à venir : `ycappuccino-ui-qt`). Une `Action` ne porte jamais de
callable Python écrit à la main : elle nomme un `Endpoint` (service/méthode/chemin), appelé génériquement
par `ycappuccino.ui.transport.perform_action` — la bibliothèque Python se limite au chargement du template
et au câblage générique des événements, jamais à la logique d'un écran particulier.

Conception : [docs/superpowers/specs/2026-09-16-ui-screen-library-checkpoint.md](../remote/docs/superpowers/specs/2026-09-16-ui-screen-library-checkpoint.md)
(brainstorming en cours, pas une spec figée — vit provisoirement dans `remote/docs/` faute d'un meilleur
endroit).

Le cœur (`model.py`/`transport.py`/`validation.py`/`loader.py`) ne dépend d'aucun toolkit de rendu ni du
reste du framework : `Screen`/`Field`/`Action`/`Endpoint` sont de simples `dataclasses`, testables sans
`ycappuccino.api`/`ycappuccino.core` installés — un choix délibéré, plus léger que de réutiliser le
mécanisme `@Item`/`@Property` de `ycappuccino.api.decorators` (pensé pour des modèles persistés via
`IManager`, ce qu'un écran n'est pas). `Endpoint(service, method, path, params)` reprend volontairement la
même forme d'adressage que `IExposedService.call(method, extra_path, params, body, subject)`
(`ycappuccino.api.endpoints_service`, déjà utilisée par `remote`) plutôt que d'en inventer une seconde.

Seul `ycappuccino_transport.py` (voir plus bas, "Ponts `ICrud`/`IServiceEndpoint`") dépend de
`ycappuccino.api` — un module séparé, optionnel : un adapter qui n'en a pas besoin ne paie rien pour que
`ycappuccino.api` soit installable.

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
`transport.call(service, method, path, params, body)`. `Transport` est un `Protocol` ; en pratique on
utilise l'un des deux ponts ci-dessous plutôt que d'en écrire un :

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

## Ponts vers les interfaces backend

`ycappuccino.ui.ycappuccino_transport` fournit les trois `Transport` qui relient un écran aux vraies
interfaces backend, injectées dans le composant qui affiche l'écran :

- `CrudTransport(crud: ICrud, subject=None)` : `service` est un `item_id` (`organization`, `role`...) ;
  `GET` sans chemin → `get_many`, `GET <id>` → `get_one`, `POST` → `create`, `PUT <id>` → `update`,
  `DELETE <id>` → `delete`.
- `ServiceEndpointTransport(endpoint: IServiceEndpoint, subject=None)` : `service` est le nom d'un service
  exposé (`login`, `change_password`...), appelé tel quel.
- `ComponentTransport(components: dict, subject=None)` : `service` nomme un des composants reçus, `method`
  est la méthode à appeler, le corps ses arguments ; le sujet est passé à une méthode qui déclare un
  paramètre `subject`. Un écran de connexion appelle ainsi `ILoginService.login` :
  `ComponentTransport({"login": login_service})` avec `endpoint: {service: login, method: login}`.

Ces ponts ne savent pas, et n'ont pas à savoir, si l'interface injectée est local ou un
proxy vers un autre framework (`ycappuccino-client` dans un navigateur) : ce choix appartient au
déploiement, jamais à `ui`. Aucune classe de `ui` ne parle HTTP.

```python
from ycappuccino.ui.ycappuccino_transport import CrudTransport

# dans un composant : def __init__(self, crud: ICrud) -> None: ...
# transport = CrudTransport(self._crud, subject=subject)
```

## Une console entière : `Application`

`ycappuccino.ui.application` décrit le layout d'une console une seule fois : écran de connexion, sections du
menu, et pour chaque entrée les écrans enchaînés. `ui_shell` et `ui_web` le rendent de la même façon.

```yaml
title: Administration
login: {screen: login, transport: login, user: login}
menu:
  - label: Utilisateurs
    entries:
      - label: Créer un utilisateur
        steps:
          - {screen: create_login, transport: services}
          - {screen: account, transport: crud, prefill: {login: values.login}}
          - {screen: role_account, transport: crud, prefill: {account: result._id}}
```

- `screen` et `transport` sont des noms que l'application résout : une fonction qui charge un `Screen` par
  son nom, et un dictionnaire de `Transport`.
- `user` (connexion) nomme le champ de l'écran de connexion dont la valeur est affichée comme utilisateur
  connecté.
- `prefill` remplit les champs d'une étape depuis la précédente : `values.<champ>` (ce qui y a été saisi) ou
  `result.<clé>` (ce que son action a renvoyé). `prefill_values(step, values, result)` fait ce calcul, et
  `with_defaults(screen, champ=valeur)` rend l'écran pré-rempli.
- Une fois connecté, l'adapter garde une barre de navigation : le titre, un menu déroulant par section,
  l'utilisateur et `sign_out` (« Se déconnecter »). Dessous : `welcome` (« Bienvenue {user}. »), puis les
  écrans d'une entrée, puis `saved` (« Enregistré. »).

## Développer ui

```bash
uv sync
uv run python -m unittest discover -s src/unittest/python
```
