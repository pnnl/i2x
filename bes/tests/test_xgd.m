function [xgd_table] = test_xgd (mpc)
  xgd_table.colnames = {
      'CommitKey', ...
      'InitialState',...
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
  wind_key = 1;  %% -1 to shut off the wind plants

  iState = 24; % so MOST can leave the unit on, or shut off immediately without a minimum up-time restriction

  gMinUp = 1;  % must be at least 1
  gMinDown = 1;
  coalUp = 12;
  coalDown = 12;
  nukeUp = 24;
  nukeDown = 24;
  gasUp = 6;
  gasDown = 6;
  peakUp = 1; % these are peaking gas generators with highest fuel cost
  peakDown = 1;

  paPrice = 0.001;
  naPrice = 0.001;
  pdPrice = 0.001;
  ndPrice = 0.001;
  plfPrice = 0.1;
  nlfPrice = 0.1;

  g1res = 19978.8;
  g2res = 11664.8;
  g3res = 2430.00;
  g4res = 20761.70;
  g5res = 3190.30;
  g6res = 2708.60;
  g7res = 80.00;
  g8res = 720.00;
  g9res = 3438.20;
  gAres = 10589.70;
  gBres = 5728.10;
  gCres = 7385.00;
  gDres = 622.4;

  w1res = 1674.80;
  w2res = 2242.20;
  w3res = 8730.30;
  w4res =   99.80;
  w5res = 3562.20;

  r1res = 2394.22;
  r2res = 2575.57;
  r3res = 54.08;
  r4res = 699.28;
  r5res = 1307.51;
  r6res = 77.34;
  r7res = 883.39;
  r8res = 18.85;

  xgd_table.data = [
  % generators
    gen_key  iState gasUp  gasDown  paPrice g1res naPrice g1res pdPrice ndPrice plfPrice g1res nlfPrice g1res;
    gen_key  iState coalUp coalDown paPrice g2res naPrice g2res pdPrice ndPrice plfPrice g2res nlfPrice g2res;
    gen_key  iState nukeUp nukeDown paPrice g3res naPrice g3res pdPrice ndPrice plfPrice g3res nlfPrice g3res;
    gen_key  iState gasUp  gasDown  paPrice g4res naPrice g4res pdPrice ndPrice plfPrice g4res nlfPrice g4res;
    gen_key  iState coalUp coalDown paPrice g5res naPrice g5res pdPrice ndPrice plfPrice g5res nlfPrice g5res;
    gen_key  iState nukeUp nukeDown paPrice g6res naPrice g6res pdPrice ndPrice plfPrice g6res nlfPrice g6res;
    gen_key  iState peakUp peakDown paPrice g7res naPrice g7res pdPrice ndPrice plfPrice g7res nlfPrice g7res;
    gen_key  iState coalUp coalDown paPrice g8res naPrice g8res pdPrice ndPrice plfPrice g8res nlfPrice g8res;
    gen_key  iState peakUp peakDown paPrice g9res naPrice g9res pdPrice ndPrice plfPrice g9res nlfPrice g9res;
    gen_key  iState gasUp  gasDown  paPrice gAres naPrice gAres pdPrice ndPrice plfPrice gAres nlfPrice gAres;
    gen_key  iState coalUp coalDown paPrice gBres naPrice gBres pdPrice ndPrice plfPrice gBres nlfPrice gBres;
    gen_key  iState gasUp  gasDown  paPrice gCres naPrice gCres pdPrice ndPrice plfPrice gCres nlfPrice gCres;
    gen_key  iState coalUp coalDown paPrice gDres naPrice gDres pdPrice ndPrice plfPrice gDres nlfPrice gDres;
  % wind plants
    wind_key iState gMinUp gMinDown paPrice w1res naPrice w1res pdPrice ndPrice plfPrice w1res nlfPrice w1res;
    wind_key iState gMinUp gMinDown paPrice w2res naPrice w2res pdPrice ndPrice plfPrice w2res nlfPrice w2res;
    wind_key iState gMinUp gMinDown paPrice w3res naPrice w3res pdPrice ndPrice plfPrice w3res nlfPrice w3res;
    wind_key iState gMinUp gMinDown paPrice w4res naPrice w4res pdPrice ndPrice plfPrice w4res nlfPrice w4res;
    wind_key iState gMinUp gMinDown paPrice w5res naPrice w5res pdPrice ndPrice plfPrice w5res nlfPrice w5res;
  % responsive loads
    resp_key iState gMinUp gMinDown paPrice r1res naPrice r1res pdPrice ndPrice plfPrice r1res nlfPrice r1res;
    resp_key iState gMinUp gMinDown paPrice r2res naPrice r2res pdPrice ndPrice plfPrice r2res nlfPrice r2res;
    resp_key iState gMinUp gMinDown paPrice r3res naPrice r3res pdPrice ndPrice plfPrice r3res nlfPrice r3res;
    resp_key iState gMinUp gMinDown paPrice r4res naPrice r4res pdPrice ndPrice plfPrice r4res nlfPrice r4res;
    resp_key iState gMinUp gMinDown paPrice r5res naPrice r5res pdPrice ndPrice plfPrice r5res nlfPrice r5res;
    resp_key iState gMinUp gMinDown paPrice r6res naPrice r6res pdPrice ndPrice plfPrice r6res nlfPrice r6res;
    resp_key iState gMinUp gMinDown paPrice r7res naPrice r7res pdPrice ndPrice plfPrice r7res nlfPrice r7res;
    resp_key iState gMinUp gMinDown paPrice r8res naPrice r8res pdPrice ndPrice plfPrice r8res nlfPrice r8res;
];
endfunction
