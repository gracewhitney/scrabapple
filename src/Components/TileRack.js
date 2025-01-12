import _ from 'lodash';
import React, {useCallback, useEffect, useState} from 'react';
import {DndProvider, useDrop} from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import Tile from "./Tile";
import {shuffle} from "../utils";


function TileRack(props) {
  const {
    gameId,
    tiles,
    returnToRackHandler,
    returnAllTilesToRackHandler,
    updateRackUrl,
  } = props

  const removedTileIds = props.removedTileIds || []

  const idTiles = tiles.map((tile, i) => {return {...tile, id: tile.id || i}})

  for (let i = idTiles.length; i < 8; i++) {
    idTiles.push({id: i })  // Add empty slots
  }

  const [rackPositions, setRackPositions] = useState([...idTiles]);
  const moveTile = (id, endingIndex) => {
    const startingIndex = rackPositions.findIndex((tile) => tile.id === id)
    const tile = rackPositions[startingIndex]
    const newRackPositions = [...rackPositions]
    if (startingIndex !== undefined) {
      newRackPositions.splice(startingIndex, 1)
    }
    newRackPositions.splice(endingIndex, 0, tile)
    setRackPositions(newRackPositions)
    if (returnToRackHandler) {
      returnToRackHandler(id)
    }
  }

  const shuffleTiles = () => {
    const newRackPositions = [...rackPositions].filter(t => t.letter !== undefined)
    shuffle(newRackPositions)
    // Add empty spaces back to end
    for (let i = newRackPositions.length; i < 8; i++) {
      newRackPositions.push({id: i })
    }
    setRackPositions(newRackPositions)
  }

  const updateRack = useCallback(
    _.debounce(async (currentRackPositions) => {
      await fetch(updateRackUrl, {
        method: 'post',
        headers: {'X-CSRFToken': window.csrfmiddlewaretoken},
        body: JSON.stringify(currentRackPositions.filter(pos => pos.letter).map(pos => pos.letter))
      })
    }, 3000),
    [],
  );

  useEffect(() => {updateRack(rackPositions)}, [rackPositions]);

  const rackAction = (
    removedTileIds.length === 0
      ? (
        <button className="btn btn-secondary my-2 me-2" onClick={shuffleTiles}>
          <span className="bi bi-shuffle"></span>
        </button>
      )
      : (
        <button className="btn btn-secondary my-2 me-2" onClick={returnAllTilesToRackHandler}>
          <span className="bi bi-arrow-down-right-square-fill"></span>
        </button>
      )
  )

  return (
    <div id="rack" className={`d-flex justify-content-center mb-3 ${gameId}-rack-container`}>
      { rackAction }
      <ul className="list-group list-group-horizontal mt-1">
        <DndProvider backend={HTML5Backend}>
          {
            rackPositions.map((tile, i) =>
              <RackPosition
                tile={removedTileIds.indexOf(tile.id) < 0 ? tile : {id: tile.id}}
                index={i}
                key={tile.id}
                moveTile={moveTile}>
              </RackPosition>
            )
          }
        </DndProvider>
      </ul>
    </div>
  );
  }


  const RackPosition = (props) => {
    const {
    tile,
    index,
    moveTile
  } = props

    const [, drop] = useDrop(
    () => ({
    accept: 'tile',
    drop: (item) => moveTile(item.id, index),
    hover({id: draggedId}) {
    if (draggedId !== tile.id) {
    moveTile(draggedId, index)
  }
  },
  }),
    [moveTile, tile.id, index]
    )

    return (
    <div ref={drop}>
    {
      tile.letter
        ? <Tile {...tile} className="list-group-item"></Tile>
        : <div className={"gap"}></div>
    }
    </div>
  )
}

export default TileRack;