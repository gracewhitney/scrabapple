import React, {useState} from 'react';
import {DndProvider, useDrop} from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import Tile from "./Tile";


function TileRack(props) {
  const {
    tiles,
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
  }

  return (
      <ul className="list-group list-group-horizontal mt-1">
        <DndProvider backend={HTML5Backend}>
        {
          rackPositions.map((tile, i) =>
            <RackPosition
              tile={removedTileIds.indexOf(tile.id) < 0 ? tile : {id: tile.id}}
              index={i} key={tile.id}
              moveTile={moveTile}>
            </RackPosition>
          )
        }
        </DndProvider>
      </ul>
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
      hover({ id: draggedId }) {
        if (draggedId !== tile.id) {
          moveTile(draggedId, index)
        }
      },
    }),
    [moveTile]
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