package com.symantec;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;


public class CheckSort {

	public static void main(String[] args) {
		int[] arr = {-1,-2,-5,-4};
		boolean sort = checkSort(arr);
		System.out.println("Sorted Array : "+sort);
		int secondHigh = secondHighest(arr);
		System.out.println("Second High : "+secondHigh);
		
		List<Integer> list1 = new ArrayList<Integer>();
		list1.add(1);
		list1.add(2);
		list1.add(2);
		list1.add(3);
		List<Integer> list2 = new ArrayList<Integer>();
		list2.add(2);
		list2.add(1);
		list2.add(2);
		list2.add(3);
		
		boolean duplicateList = checkSameList(list1, list2);
	}
	
	private static boolean checkSameList(List<Integer> list1,
			List<Integer> list2) {
		boolean duplicate = false;
		Map<Integer, Integer> map1 = new HashMap<Integer, Integer>();
		Map<Integer, Integer> map2 = new HashMap<Integer, Integer>();
		if (list1.size() == list2.size()){
			int j=0;
			for (Integer i : list1){
				if(map1.containsKey(i)){
					int value = map1.get(i);
					value++;
					map1.put(i, value);
				}
				else
				{
					map1.put(i, i);
				}
			}
		}
		
		return duplicate;
	}

	static int reverseNumber(int num){
		int reverse =0;
		while(num !=0){
			reverse = (reverse*10) + (num%10);
			num = num/10;
		}
		
		return reverse;
	}
	
	static boolean checkSort(int[] arr)
	{
		boolean sorted = true;
		
		for (int i=1; i<arr.length; i++){
			if (arr[i] < arr[i-1])
			{
				return false;
			}
		}
		
		return sorted;
	}
	
	static int secondHighest(int[] arr) {
		Integer secondHighest = 0;
		if (arr.length > 0) {
			Integer highest = Integer.MIN_VALUE+1;
			secondHighest = Integer.MIN_VALUE;
			for (int i = 0; i < arr.length; i++) {
				if (arr[i] > highest) {
					secondHighest = highest;
					highest = arr[i];
				} else if (arr[i] > secondHighest) {
					secondHighest = arr[i];
				}
			}
		}
		return secondHighest;
	}

}
