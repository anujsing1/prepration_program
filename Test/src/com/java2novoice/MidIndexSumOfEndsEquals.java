package com.java2novoice;

public class MidIndexSumOfEndsEquals {

	public static void main(String[] args) {
		// TODO Auto-generated method stub

	}

	private static int findMiddleIndex(int[] arr){
		int midIndex = 0;
		int startIndex = 0;
		int endIndex = arr.length-1;
		int sumLeft = 0;
		int sumRight = 0;
		while(true){
			if (sumLeft > sumRight){
				sumRight += arr[endIndex--];
			}else {
				sumLeft += arr[startIndex++];
			}
			
			if(startIndex > endIndex){
				if(sumLeft == sumRight){
					midIndex = endIndex;
					break;
				}
				else
					break;
			}
		}
		return midIndex;
	}
	
}
