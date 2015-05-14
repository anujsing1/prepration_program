package com.groupon;

public class NthMinValInArr {

	public static void main(String[] args) {
		int[] arr = {5, 10, 1, -10, 3, -4};
		sortArray(arr);
		for(int val:arr){
			System.out.println(val);
		}
		int n = 4;
		System.out.println("Nth min value is : "+arr[n-1]);
	}
	
	static void sortArray(int[] arr){
		for(int i=0;i<arr.length;i++){
			for (int j=1;j<arr.length;j++){
				if(arr[j]<arr[j-1]){
					int temp = arr[j-1];
					arr[j-1] = arr[j];
					arr[j] = temp;
				}
			}
		}
	}

}
