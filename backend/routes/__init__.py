"""Blueprints de la API REST; todos se publican bajo /api."""
from routes import (auth, catalogos, complejos, equipos, jugadores, partidos,
                    planillas, reportes, sanciones, torneos)

BLUEPRINTS = (auth.bp, catalogos.bp, jugadores.bp, torneos.bp, equipos.bp, complejos.bp,
              partidos.bp, planillas.bp, sanciones.bp, reportes.bp)
