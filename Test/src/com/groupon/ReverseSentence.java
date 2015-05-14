package com.groupon;

public class ReverseSentence {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		System.out.println(reverseSentence("Test is Successful"));
	}

	static StringBuilder reverseSentence(String sentence){
		String[] str = sentence.split(" ");
		StringBuilder reverseString = new StringBuilder();
		for(int i=str.length-1;i>=0;i--){
			reverseString.append(str[i] + " ");
		}
		return reverseString;
	}
	
}
