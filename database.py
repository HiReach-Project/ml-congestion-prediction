# Congestion API - a REST API built to track congestion spots and
# crowded areas using real-time location data from mobile devices.
#
# Copyright (C) 2020, University Politehnica of Bucharest, member
# of the HiReach Project consortium <https://hireach-project.eu/>
# <andrei[dot]gheorghiu[at]upb[dot]ro. This project has received
# funding from the European Union’s Horizon 2020 research and
# innovation programme under grant agreement no. 769819.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine('postgres+psycopg2://postgres:postgres@localhost:5432/ml_prediction')

db_session = scoped_session(sessionmaker(bind=engine))
