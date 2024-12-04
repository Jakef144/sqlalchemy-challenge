from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
import datetime as dt

#################################################
# Flask Setup
#################################################

# Create Flask app
app = Flask(__name__)

#################################################
# Database Setup
#################################################

# Set up database connection
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect the database into ORM classes
Base = automap_base()
Base.prepare(engine, reflect=True)

# Reference the tables
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available API routes."""
    return (
        f"Welcome to the Hawaii Climate API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt;<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;<br/>"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the last 12 months of precipitation data as JSON."""
    session = Session(engine)
    # Get the most recent date in the dataset
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    one_year_ago = dt.datetime.strptime(most_recent_date, "%Y-%m-%d") - dt.timedelta(days=365)

    # Query the precipitation data
    results = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= one_year_ago).all()
    session.close()

    # Convert results into a dictionary
    precipitation_data = {date: prcp for date, prcp in results}
    return jsonify(precipitation_data)


@app.route("/api/v1.0/stations")
def stations():
    """Return a list of all stations."""
    session = Session(engine)
    results = session.query(Station.station).all()
    session.close()

    # Convert list of tuples into a list
    station_list = [station[0] for station in results]
    return jsonify(station_list)


@app.route("/api/v1.0/tobs")
def tobs():
    """Return the last 12 months of temperature observations for the most active station."""
    session = Session(engine)

    # Get the most active station
    most_active_station = (
        session.query(Measurement.station)
        .group_by(Measurement.station)
        .order_by(func.count(Measurement.station).desc())
        .first()[0]
    )

    # Get the most recent date in the dataset
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    one_year_ago = dt.datetime.strptime(most_recent_date, "%Y-%m-%d") - dt.timedelta(days=365)

    # Query the temperature observations for the most active station
    results = session.query(Measurement.tobs).filter(Measurement.station == most_active_station).filter(Measurement.date >= one_year_ago).all()
    session.close()

    # Convert list of tuples into a list
    tobs_data = [tobs[0] for tobs in results]
    return jsonify(tobs_data)


@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_stats(start, end=None):
    """Return min, avg, and max temperature for a specified start or start-end range."""
    session = Session(engine)

    # Define the query
    if not end:
        results = session.query(
            func.min(Measurement.tobs),
            func.avg(Measurement.tobs),
            func.max(Measurement.tobs)
        ).filter(Measurement.date >= start).all()
    else:
        results = session.query(
            func.min(Measurement.tobs),
            func.avg(Measurement.tobs),
            func.max(Measurement.tobs)
        ).filter(Measurement.date >= start).filter(Measurement.date <= end).all()

    session.close()

    # Convert results into a dictionary
    temp_stats = {
        "TMIN": results[0][0],
        "TAVG": results[0][1],
        "TMAX": results[0][2]
    }
    return jsonify(temp_stats)


#################################################
# Run the Flask App
#################################################

if __name__ == "__main__":
    app.run(debug=True)
