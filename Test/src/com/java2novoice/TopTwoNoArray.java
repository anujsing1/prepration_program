package com.java2novoice;

public class TopTwoNoArray {

	public static void main(String[] args) {
		int[] arr = {-5, -7, 10, 100, 5, 10, 11, -400};
		printTopTwo(arr);
	}

	static void printTopTwo(int arr[]){
		int max = Integer.MIN_VALUE+1;
		int secMax = Integer.MIN_VALUE;
		
		for(int i=0;i<arr.length;i++){
			if(arr[i] > max){
				secMax = max;
				max = arr[i];
			}else if(arr[i] > secMax){
				secMax = arr[i];
			}
		}
		System.out.println("Max : "+max +" & Second Max : "+secMax);
	}
	
}
