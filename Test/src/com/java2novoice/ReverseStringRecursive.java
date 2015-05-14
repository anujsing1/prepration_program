package com.java2novoice;

public class ReverseStringRecursive {

	static String reverse = "";
	public static void main(String[] args) {
		reverse = reverseString("Test");
		System.out.println("Rev Str : " + reverse);
	}

	private static String reverseString(String str){
		int endIndex = str.length();
		if (endIndex == 1)
			return str;
		else
			reverse += str.charAt(str.length()-1) + reverseString(str.substring(0, str.length()-1));
			
		return reverse;
	}
}
