/**
 * 
 */
package com.programming.array;

import java.util.Arrays;

/**
 * @author govind.gupta
 *
 */
public class SumOfTwoNum {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		// TODO Auto-generated method stub
		int sum = 15;
		int[] arr = {11, 15, 6, 8, 9, 10};
		int l=0, r=arr.length-1;
		Arrays.sort(arr);
		while (l < r)
		{
			if ((arr[l] + arr[r]) == sum)
			{
				System.out.println(arr[l] + " : " +arr[r]);
				break;
			}
			else if ((arr[l] + arr[r]) < sum)
				l++;
			else 
				r--;
		}
	}

}
