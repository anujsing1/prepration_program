package com.parantap;


public class DeletingSubString {

	public static void main(String[] args) {
		String str = "aabcbdc";
		String t = "abc";
	    int n = str.length();
	    int strLen = t.length();
	    
	    StringBuilder sb = new StringBuilder(str);
	    int counter=0;

	    for (int i = 0; i < n; )
	    {
	    	if(i+strLen <= n)
	    	{
		    	if(t.equalsIgnoreCase(sb.substring(i, strLen+i)))
		    	{
		    		sb.replace(i, strLen+i, "");
		    		n = sb.length();
		    		counter++;
		    		i=0;
		    		continue;
		    	}
	    	}
	    	i++;
	    }
		System.out.println(counter);
	}
}
