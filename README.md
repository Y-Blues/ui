# ycappuccino-ui

Une bibliothèque de description d'écran, pas un toolkit graphique : un `Screen` décrit un formulaire
(champs + actions) une seule fois, en Python pur, sans savoir s'il sera rendu en shell, en Qt ou dans un
navigateur — le rendu est le rôle des adapters séparés (`ycappuccino-ui-shell` pour le terminal, à
venir : `ycappuccino-ui-qt`, `ycappuccino-ui-web`).

Conception : [docs/superpowers/specs/2026-09-16-ui-screen-library-checkpoint.md](../remote/docs/superpowers/specs/2026-09-16-ui-screen-library-checkpoint.md)
(brainstorming en cours, pas une spec figée — vit provisoirement dans `remote/docs/` faute d'un meilleur
endroit).

Aucune dépendance à `ycappuccino.api`/`ycappuccino.core` : `Screen`/`Field`/`Action` sont de simples
`dataclasses`, testables sans aucun toolkit de rendu installé et sans le reste du framework — un choix
délibéré, plus léger que de réutiliser le mécanisme `@Item`/`@Property` de `ycappuccino.api.decorators`
(pensé pour des modèles persistés via `IManager`, ce qu'un écran n'est pas).

## Décrire un écran

```python
from ycappuccino.ui.model import Action, Field, Screen

def log_in(values: dict) -> None:
    print(f"logging in as {values['username']!r}")

screen = Screen(
    title="Connexion",
    fields=(
        Field(name="username", label="Nom d'utilisateur", required=True),
        Field(name="remember_me", label="Se souvenir de moi", type="boolean", default=False),
    ),
    actions=(Action(name="submit", label="Se connecter", handler=log_in),),
)
```

Types de champ disponibles (`Field.type`) : `"text"` (défaut), `"number"`, `"boolean"`, `"choice"`
(nécessite `choices=(...)`, non vide), `"date"`.

## Valider

`validate_screen(screen, values)` applique `required` et l'éventuel `Field.validate` (un callable
`valeur -> message d'erreur ou None`) — la même logique pour tous les adapters, jamais réimplémentée par
renderer :

```python
from ycappuccino.ui.validation import validate_screen

errors = validate_screen(screen, {"username": ""})
# {"username": "Nom d'utilisateur is required"}
```

`Field.validate` n'est appelé que si le champ n'est pas vide (`required` couvre déjà le cas vide) —
`Field.default` sert de valeur de repli si la clé est absente de `values`.

## Développer ui

```bash
uv sync
uv run python -m unittest discover -s src/unittest/python
```
