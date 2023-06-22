function [xgd_table] = test_xgd (mpc)
  xgd_table.colnames = {
      'CommitKey', ...
      'MinUp', ...
      'MinDown', ...
      'PositiveActiveReservePrice', ...
      'PositiveActiveReserveQuantity', ...
      'NegativeActiveReservePrice', ...
      'NegativeActiveReserveQuantity', ...
      'PositiveActiveDeltaPrice', ...
      'NegativeActiveDeltaPrice', ...
      'PositiveLoadFollowReservePrice', ...
      'PositiveLoadFollowReserveQuantity', ...
      'NegativeLoadFollowReservePrice', ...
      'NegativeLoadFollowReserveQuantity', ...
  };
  gen_key = 1;
  resp_key = 2;
%  wind_key = -1;
  wind_key = 1;

  gMinUp = 1;  % must be GE 1
  gMinDown = 1;

  paPrice = 0.001;
  naPrice = 0.001;
  pdPrice = 0.001;
  ndPrice = 0.001;
  plfPrice = 0.1;
  nlfPrice = 0.1;

  g1res = 8000.0;
  g2res = 4000.0;
  g3res =  200.0;
  g4res = 9000.0;
  g5res =  500.0;
  g6res =  200.0;
  g7res =   40.0;
  g8res =  300.0;
  g9res = 1500.0;
  gAres = 5000.0;
  gBres = 3000.0;
  gCres = 3000.0;
  gDres =  300.0;

  w1res =  800.0;
  w2res = 1100.0;
  w3res = 4300.0;
  w4res =   50.0;
  w5res = 1700.0;

  r1res = 2000.0;
  r2res = 4000.0;
  r3res =  100.0;
  r4res = 1000.0;
  r5res = 1000.0;
  r6res =  100.0;
  r7res = 1000.0;
  r8res =  100.0;

  xgd_table.data = [
  % generators
    gen_key  gMinUp gMinDown paPrice g1res naPrice g1res pdPrice ndPrice plfPrice g1res nlfPrice g1res;
    gen_key  gMinUp gMinDown paPrice g2res naPrice g2res pdPrice ndPrice plfPrice g2res nlfPrice g2res;
    gen_key  gMinUp gMinDown paPrice g3res naPrice g3res pdPrice ndPrice plfPrice g3res nlfPrice g3res;
    gen_key  gMinUp gMinDown paPrice g4res naPrice g4res pdPrice ndPrice plfPrice g4res nlfPrice g4res;
    gen_key  gMinUp gMinDown paPrice g5res naPrice g5res pdPrice ndPrice plfPrice g5res nlfPrice g5res;
    gen_key  gMinUp gMinDown paPrice g6res naPrice g6res pdPrice ndPrice plfPrice g6res nlfPrice g6res;
    gen_key  gMinUp gMinDown paPrice g7res naPrice g7res pdPrice ndPrice plfPrice g7res nlfPrice g7res;
    gen_key  gMinUp gMinDown paPrice g8res naPrice g8res pdPrice ndPrice plfPrice g8res nlfPrice g8res;
    gen_key  gMinUp gMinDown paPrice g9res naPrice g9res pdPrice ndPrice plfPrice g9res nlfPrice g9res;
    gen_key  gMinUp gMinDown paPrice gAres naPrice gAres pdPrice ndPrice plfPrice gAres nlfPrice gAres;
    gen_key  gMinUp gMinDown paPrice gBres naPrice gBres pdPrice ndPrice plfPrice gBres nlfPrice gBres;
    gen_key  gMinUp gMinDown paPrice gCres naPrice gCres pdPrice ndPrice plfPrice gCres nlfPrice gCres;
    gen_key  gMinUp gMinDown paPrice gDres naPrice gDres pdPrice ndPrice plfPrice gDres nlfPrice gDres;
  % wind plants
    wind_key gMinUp gMinDown paPrice w1res naPrice w1res pdPrice ndPrice plfPrice w1res nlfPrice w1res;
    wind_key gMinUp gMinDown paPrice w2res naPrice w2res pdPrice ndPrice plfPrice w2res nlfPrice w2res;
    wind_key gMinUp gMinDown paPrice w3res naPrice w3res pdPrice ndPrice plfPrice w3res nlfPrice w3res;
    wind_key gMinUp gMinDown paPrice w4res naPrice w4res pdPrice ndPrice plfPrice w4res nlfPrice w4res;
    wind_key gMinUp gMinDown paPrice w5res naPrice w5res pdPrice ndPrice plfPrice w5res nlfPrice w5res;
  % responsive loads
    resp_key gMinUp gMinDown paPrice r1res naPrice r1res pdPrice ndPrice plfPrice r1res nlfPrice r1res;
    resp_key gMinUp gMinDown paPrice r2res naPrice r2res pdPrice ndPrice plfPrice r2res nlfPrice r2res;
    resp_key gMinUp gMinDown paPrice r3res naPrice r3res pdPrice ndPrice plfPrice r3res nlfPrice r3res;
    resp_key gMinUp gMinDown paPrice r4res naPrice r4res pdPrice ndPrice plfPrice r4res nlfPrice r4res;
    resp_key gMinUp gMinDown paPrice r5res naPrice r5res pdPrice ndPrice plfPrice r5res nlfPrice r5res;
    resp_key gMinUp gMinDown paPrice r6res naPrice r6res pdPrice ndPrice plfPrice r6res nlfPrice r6res;
    resp_key gMinUp gMinDown paPrice r7res naPrice r7res pdPrice ndPrice plfPrice r7res nlfPrice r7res;
    resp_key gMinUp gMinDown paPrice r8res naPrice r8res pdPrice ndPrice plfPrice r8res nlfPrice r8res;
];
endfunction
