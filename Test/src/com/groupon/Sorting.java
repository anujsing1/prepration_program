package com.groupon;

public class Sorting {

	public static void main(String[] args) {
		int arr[] = {4,2,15,-1,7};
		selectionSort(arr);
		insertionSort(arr);
	}

	
	static void selectionSort(int[] arr)
	{
		for (int i=0;i<arr.length;i++){
			int minPos =i;
			for(int j=i+1;j<arr.length;j++){
				if(arr[j] < arr[minPos])
				{
					minPos = j;
				}
			}
			if (minPos != 0) {
				int temp = arr[i];
				arr[i] = arr[minPos];
				arr[minPos] = temp;
			}
		}
		for(int a:arr){
			System.out.println(a);
		}
	}
	
	static void insertionSort(int[] arr){
		for (int i=1;i<arr.length;i++){
			for(int j=i;j>0;j--){
				if(arr[j] < arr[j-1]){
					int temp = arr[j-1];
					arr[j-1] = arr[j];
					arr[j] = temp;
				}
			}
		}
		for(int a:arr){
			System.out.println(a);
		}
	}
	
	
	
}
