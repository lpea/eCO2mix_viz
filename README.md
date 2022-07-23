# eCO2mix_viz

Affiche les données de puissance de RTE éCO2mix sous forme d'un graphique interactif similaire à
celui disponible sur le [site de RTE](https://www.rte-france.com/eco2mix/la-production-delectricite-par-filiere).

## Utilisation

```bash
python plot.py eCO2mix_RTE_En-cours-Consolide.zip [--static]
```

Le script lance un serveur HTTP avec Dash, accessible par défaut à l'adresse http://127.0.0.1:8050/.

Le mot-clé ``static`` affiche un graphique statique avec ``matplotlib``. Les dates de début et de
fin de période ainsi que le pas de temps ne sont pas configurables et doivent être changés
directement dans le script.

### Dépendances

Le script nécessite les paquets python `plotly`, `dash`, `pandas` et `matplotlib` (optionnel).

```bash
pip install --user plotly dash pandas [matplotlib]
```

### Fichiers de données

Les fichiers de données peuvent être téléchargés à la page suivante : [Télécharger les indicateurs](https://www.rte-france.com/eco2mix/telecharger-les-indicateurs).

**Attention, le script ne fonctionne qu'avec les fichiers de données « puissance » suivants :**

* En-cours mensuel temps réel
* En-cours annuel consolidé
* Annuel définitif YYYY

[Description des données](https://assets.rte-france.com/prod/public/2020-07/%C3%A9CO2mix%20-%20Description%20des%20fichiers%20des%20donn%C3%A9es%20en%20puissance.pdf)

