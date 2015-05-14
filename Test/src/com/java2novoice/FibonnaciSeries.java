package com.java2novoice;

public class FibonnaciSeries {

	public static void main(String[] args) {
		printFibonnaciSeries(8);
	}

	static void printFibonnaciSeries(int num){
		int feb1=1;
		int feb2=1;
		for (int i=0; i<num;i++){
			if(i == 0 || i == 1)
				System.out.print(1+", ");
			else{
				int feb = feb1+feb2;
				feb2=feb1;
				feb1=feb;
				System.out.print(feb + ", ");
			}
		}
	}
	
}
