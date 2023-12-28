import React from 'react';
import GameBoard from "../Components/GameBoard";

const ScrabbleGame = (props) => {
  return <GameBoard {...props} gameId="scrabble"/>
}

export default ScrabbleGame;