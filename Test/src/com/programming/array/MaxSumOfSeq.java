/**
 * 
 */
package com.programming.array;


/**
 * @author govind.gupta
 *
 */
public class MaxSumOfSeq {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		// TODO Auto-generated method stub
		int[] array = new int[] {10,5,2,-6,7,-4, 3};
		int max = max_sum(array);
		System.out.println(max);
		array = new int[] {-2, 1, -3, 4, -1, 2, 1, -5, 6};
//		array = new int[] {-2, -1, -3, -4, -1, -2, -1, -5, -4};
		max = largestSubSequence(array);
		System.out.println(max);
	}
	
	static int max_sum(int[] array) {
	    int total = 0, min_sum = Integer.MAX_VALUE, max_sum =Integer.MIN_VALUE, min_diff=Integer.MAX_VALUE, max_diff=Integer.MIN_VALUE;
	    for (int i = 0; i < array.length; i++) {
	        total += array[i];
	        min_sum = Math.min(min_sum, total);
	        max_sum = Math.max(max_sum, total);
	        min_diff = Math.min(min_diff, total - max_sum);
	        max_diff = Math.max(max_diff, total - min_sum);
	    }
	    return Math.max(max_diff, total - min_diff);
	}
	
	static int largestSubSequence(int[] array)
	{
	    int currSum = 0;
	    int maxSum = Integer.MIN_VALUE; // or something else large and negative
	    int firstIndex = 0, lastIndex = 0;
	    for(int i = 0; i < array.length; i++)
	    {
	        currSum = currSum + array[i];
	        
	        if(currSum > maxSum) 
	        {
	            maxSum = currSum;
	            lastIndex = i;
	        }
	        
	        if(currSum < 0) 
	        {
	            currSum = 0;
	            firstIndex = i+1;
	        }
	    }
	    if (lastIndex < firstIndex)
	    	firstIndex = lastIndex;
	    System.out.println("lastIndex = " + lastIndex + "firstIndex = "+firstIndex);
	    return maxSum;    
	}

}
