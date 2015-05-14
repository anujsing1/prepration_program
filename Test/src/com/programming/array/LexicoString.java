package com.programming.array;

import java.util.Arrays;

public class LexicoString {

	public static void main(String[] args) {
		
		String str = "abcdba";
		String str1 = "baabccd";
	    int n = str1.length();
	    
	    // Create an array of strings to store all rotations
	    String[] arr = new String[n];
	 
	    // Create a concatenation of string with itself
	    String concat = str1 + str1;
	 
	    // One by one store all rotations of str in array.
	    // A rotation is obtained by getting a substring of concat
	    for (int i = 0; i < n; i++)
	    {
	        arr[i] = concat.substring(i, n+i)+i;
	    }
		
	    Arrays.sort(arr);
	    System.out.println(arr[0].charAt(n));
	    System.out.println(arr[0].charAt(n) - '0');
	}

}
