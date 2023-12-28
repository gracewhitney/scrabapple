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
  const displayLetter = blank ? (letter.length > 1 ? letter[1] : '') : letter[0]

  const points = TILE_SCORES[letter[0]]

  const [{isDragging}, drag] = useDrag(() => ({
    type: 'tile',
    item: {
      ...props
    },
    canDrag: () => {return id !== undefined},
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging()
    })
  }), [id, letter])

  const underTile = (
    blank || letter.length <= 1
      ? null
      : <div className={`tile height-${letter.length - 1}`}>{ letter[1] }</div>
  )

  return (
    <>
    {underTile}
    <li className={`${className || ''} ${letter[0]} height-${letter.length} tile${blank ? ' blank' : ''}${isDragging ? ' dragging': ''}`} ref={drag}>
      <div className="height-container">
        {[...Array(letter.length).keys()].map(i => <div className="height-marker" key={i}></div>)}
      </div>
      { displayLetter
        ? <span>{ displayLetter }<span className="tile-score">{ points || '' }</span></span>
        : null
      }
    </li>
    </>
  )
}

export default Tile;