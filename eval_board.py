def eval_board(board, colour, score_normalised):
    # Perform a static evaluation of the board
    # Uses the NEGA-MAX framework
    # Returns a score for the board relative to the player to move

    score = 0

    # define pawn types
    blocked = 0
    doubled = 0
    isolated = 0

    mobility = 0
    """
        f(p) = 200(K-K')
           + 9(Q-Q')
           + 5(R-R')
           + 3(B-B' + N-N')
           + 1(P-P')
           - 0.5(D-D' + S-S' + I-I')
           + 0.1(M-M') + ...

    KQRBNP = number of kings, queens, rooks, bishops, knights and pawns
    D,S,I = doubled, blocked and isolated pawns
    M = Mobility (the number of legal moves)
    """

    # Count the number of kings, queens, rooks, bishops, knights and pawns
    for i in (0, 7):
        for x in range(0, 7):
            try:
                if board[i][x].__class__.__name__ == "King":
                    if board[i][x].colour == colour:
                        score += 200
                    else:
                        score -= 200

                elif board[i][x].__class__.__name__ == "Queen":
                    if board[i][x].colour == colour:
                        score += 9
                    else:
                        score -= 9

                elif board[i][x].__class__.__name__ == "Rook":
                    if board[i][x].colour == colour:
                        score += 5
                    else:
                        score -= 5

                elif (
                    board[i][x].__class__.__name__ == "Bishop"
                    or board[i][x].__class__.__name__ == "Knight"
                ):
                    if board[i][x].colour == colour:
                        score += 3
                    else:
                        score -= 3

                elif board[i][x].__class__.__name__ == "Pawn":
                    if board[i][x].colour == colour:
                        score += 1
                    else:
                        score -= 1

                    # Doubled pawns
                    if board[i][x + 1].__class__.__name__ == "Pawn":
                        if board[i][x + 1].colour == colour:
                            doubled -= 0.5
                        else:
                            doubled += 0.5
                    if board[i][x - 1].__class__.__name__ == "Pawn":
                        if board[i][x - 1].colour == colour:
                            doubled -= 0.5
                        else:
                            doubled += 0.5

                    # Blocked pawns
                    # check if ther is a piece infrount of the pawn
                    if board[i][x].colour == "white":
                        if board[i + 1][x].__class__.__name__ != "":
                            match colour:
                                case "white":
                                    blocked -= 0.5
                                case "black":
                                    blocked += 0.5

                    elif board[i][x].colour == "black":
                        if board[i - 1][x].__class__.__name__ != "":
                            match colour:
                                case "white":
                                    blocked += 0.5
                                case "black":
                                    blocked -= 0.5

                    # Isolated pawns
                    # Check for white isolated pawns
                    if board[i][x].colour == "white":
                        if board[i + 1][x + 1].__class__.__name__ == "Pawn":
                            if board[i + 1][x + 1].colour == "white":
                                match colour:
                                    case "white":
                                        isolated -= 0.5
                                    case "black":
                                        isolated += 0.5
                        if board[i + 1][x - 1].__class__.__name__ == "Pawn":
                            if board[i + 1][x - 1].colour == "white":
                                match colour:
                                    case "white":
                                        isolated -= 0.5
                                    case "black":
                                        isolated += 0.5

                    # Check for black isolated pawns
                    if board[i][x].colour == "black":
                        if board[i - 1][x + 1].__class__.__name__ == "Pawn":
                            if board[i - 1][x + 1].colour == "black":
                                match colour:
                                    case "white":
                                        isolated -= 0.5
                                    case "black":
                                        isolated += 0.5
                        if board[i - 1][x - 1].__class__.__name__ == "Pawn":
                            if board[i - 1][x - 1].colour == "black":
                                match colour:
                                    case "white":
                                        isolated -= 0.5
                                    case "black":
                                        isolated += 0.5
            except TypeError:
                # No piece at this position
                pass

            # Calculate mobility
            try:
                if board[i][x].colour == colour:
                    mobility += len(board[i][x].get_moves(board, (i, x)))
                else:
                    mobility -= len(board[i][x].get_moves(board, (i, x)))
            except AttributeError:
                # No piece at this position
                pass
            except Exception as e:
                print(e)

    score -= 0.5 * (doubled + blocked + isolated)
    score += 0.1 * mobility
    
    if score_normalised:
        # modify score to be between 0 - 1
        score = 1 / (1 + 10 ** (-score / 400))

    # log the score
    print(f"Evaluated board score: {score}")

    return score
