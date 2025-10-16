from app import create_app, db
from app.models.movie import Movie

app = create_app()

with app.app_context():
    print('App context ready. Querying up to 10 movies...')
    movies = Movie.query.order_by(Movie.num).limit(10).all()
    print('Found', len(movies), 'movies')
    for m in movies:
        print('NUM', m.num)
        print('  dateadded (raw):', repr(m.dateadded), 'type:', type(m.dateadded))
        try:
            print('  dateadded_str():', m.dateadded_str())
        except Exception as e:
            print('  dateadded_str() ERROR:', e)
        print('  datewatched (raw):', repr(m.datewatched), 'type:', type(m.datewatched))
        try:
            print('  datewatched_str():', m.datewatched_str())
        except Exception as e:
            print('  datewatched_str() ERROR:', e)
        print('---')

    if not movies:
        print('No movies to show; perhaps the table is empty. You can run the legacy import or add a movie via the UI.')
