package com.hackerearth;

public class NoOfRs {

	public static void main(String[] args) {
		String str = "RKRKRRKKR";
		char[] rks = str.toCharArray();
		int[] sum = new int[str.length()];
		int currSum = 0;
	    int maxSum = Integer.MIN_VALUE;
	    int firstIndex = 0, lastIndex = 0;
		for(int i=0;i<str.length();i++)
		{
			if(rks[i] == 'K')
				sum[i] = 1;
			else if(rks[i] == 'R')
				sum[i] = -1;
			
			currSum = currSum + sum[i];
	        
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
		
		for(int i=firstIndex; i<=lastIndex; i++)
		{
			if (rks[i] == 'K')
				rks[i] = 'R';
			else 
				rks[i] = 'K';
		}
		System.out.println(rks);
	}
	
	static int largestSubSequence(int[] array, int firstIndex, int lastIndex)
	{
	    int currSum = 0;
	    int maxSum = Integer.MIN_VALUE; // or something else large and negative
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
