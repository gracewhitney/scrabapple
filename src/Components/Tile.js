import React from 'react';
import {useDrag} from "react-dnd";
import {TILE_SCORES} from "../constants";

const Tile = (props) => {
  const {
    letter,
    id,
    className,
  } = props;

  const blank = letter[0] === '-'
  const displayLetter = blank ? (letter.length > 1 ? letter[1] : '') : letter

  const points = TILE_SCORES[letter[0]]

  const [{isDragging}, drag] = useDrag(() => ({
    type: 'tile',
    item: {
      ...props
    },
    canDrag: () => id !== undefined,
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging()
    })
  }))

  return (
    <li className={`${className} scrabble-tile${blank ? ' blank' : ''}${isDragging ? ' dragging': ''}`} ref={drag}>
      { displayLetter
        ? <span>{ displayLetter }<span className="tile-score">{ points || '' }</span></span>
        : null
      }
    </li>
  )
}

export default Tile;