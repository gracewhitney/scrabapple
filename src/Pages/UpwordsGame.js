import React from 'react';
import GameBoard from "../Components/GameBoard";

const UpwordsGame = (props) => {
  return <GameBoard {...props} gameId="upwords" stackHeight={5}/>
}

export default UpwordsGame;