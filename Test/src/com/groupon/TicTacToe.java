package com.groupon;

public class TicTacToe {

	private static String board[][];
	public static void main(String[] args) {
		board = new String[3][3];
		
		int row = 1, col = 2;
		boolean win = checkWin(board, row, col);
		if(!win){
			boolean gameDraw = checkLastMove(board);
			if(gameDraw)
				System.out.println("Game is Drawn");
			else
				System.out.println("Game is still on");
		}
		else
			System.out.println("Win");
	}

	
	static boolean checkWin(String[][] board,int row, int col){
		if(board[row][0] == board[row][1] && board[row][0] == board[row][2])
			return true;
		if(board[0][col] == board[1][col] && board[0][col] == board[2][col])
			return true;
		if(row==col){
			if(board[0][0] == board[1][1] && board[0][0] == board[2][2])
				return true;
		}
		return false;
	}
	
	static boolean checkWinForNPlayer(String[][] board, int row, int col, int n) {
		boolean rowEqual = true, colEqual = true, rDigEqual = true, lDigEqual = true;
		int len = n-1;
		for (int i = 0; i < n; i++) {
			if (rowEqual && board[row][col] != board[row][i])
				rowEqual = false;
			if (colEqual && board[row][col] != board[i][col])
				colEqual = false;
			if (rDigEqual && row == col) {
				if (board[row][col] != board[i][i])
					rDigEqual = false;
			}
			if (lDigEqual && (row+col) == (board.length -1)) {
				if (board[row][col] != board[i-1][len])
					lDigEqual = false;
				len--;
			}
		}
		return (rowEqual || colEqual || rDigEqual || lDigEqual);
	}
	
	static boolean checkLastMove(String[][] board){
		for(int i=0;i<3;i++){
			for(int j=0;j<3;j++){
				if(null == board[i][j] && board[i][j].equalsIgnoreCase("-"))
					return false;
			}
		}
		return true;
	}
	
	
		static boolean checkD1(int[][] board, int x, int y, int player) {
	        boolean result = false;
	        if(x!=y) {
	                return result;
	        } else {
	                result = true;
	                for(int i = 0 ; i<3 ; i++) {
	                        if(board[i][i] != player) {
	                                result = false;
	                                break;
	                        }
	                }
	        }
	        return result;
	}
	
	static boolean checkD2(int[][] board, int x, int y, int player) {
	        boolean result =false;
	        if((x+y) != (board.length -1)) {
	                return result;
	        } else {
	                result = true;
	                for(int i = 0 ; i<3 ; i++) {
	                        if(board[i][board.length-i-1] != player) {
	                                result = false;
	                                break;
	                        }
	                }
	        }
	        return result;
	}
	
	static boolean checkHorizontal(int[][] board, int x, int y, int player) {
	        boolean result = true;
	        for(int i = 0 ; i<3 ; i++) {
	                if(board[i][y] != player) {
	                        result = false;
	                        break;
	                }
	        }
	        return result;
	}
	
	static boolean checkVertical(int[][] board, int x, int y, int player) {
	        boolean result = true;
	        for(int i = 0 ; i<3 ; i++) {
	                if(board[x][i] != player) {
	                        result = false;
	                        break;
	                }
	        }
	        return result;
	}
}
