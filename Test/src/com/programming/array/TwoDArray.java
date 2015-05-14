package com.programming.array;

public class TwoDArray {

	public static void main(String[] args) {
		int[][] arr = {{3,2,6,1},
						{4,56,1,45},
						{31,32,33,34}
					  };
		System.out.println(arr.length);
		System.out.println(arr[0].length);
		
		for(int i:arr[1]){
			System.out.println(i);
		}

	}

}
