# SHFA
This is an application for the GRIDH Django database coordination solution Diana.

## Data
The data was created from JSON files with a predetermined structure. To load the data, use the `load_shfa` management command:

```bash
python manage.py load_shfa -b <path-to-json-image-records>
```
This will load the data into the database and connect it to precomputed sites. If you also need to load some sites from a source, use
```bash
python manage.py load_shfa -b <path-to-json-image-records> -s <path-to-json-site-records>
```
