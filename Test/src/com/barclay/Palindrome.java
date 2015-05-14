package com.barclay;

import java.util.ArrayList;
import java.util.List;

public class Palindrome {

	public static void main(String[] args) {
		String str = "ababa";
		System.out.println(isPalindrome(str));
		palindromeStrings("ccabadda");
	}

	static boolean isPalindrome(String str){
		boolean palindrome = true;
		str = str.toLowerCase();
		for(int i=0,j=str.length()-1;;i++,j--){
			if(i<j){
				if (str.charAt(i) != str.charAt(j)){
					palindrome = false;
					break;
				}
			}
			else{
				break;
			}
		}
		return palindrome;
	}
	
	static void palindromeStrings(String word){
		int len = word.length();
		int beginIndex=0;
		int gap=3;
		List<String> palinStrings = new ArrayList<String>();
		while(len>2){
			if(beginIndex + gap > len){
				beginIndex = 0;
				gap = gap+1;
			}
			if(beginIndex+gap > len)
				break;
			String temp = word.substring(beginIndex, beginIndex+gap);
			if(isPalindrome(temp)){
				palinStrings.add(temp);
			}
			beginIndex++; 
		}
		
		for(String str : palinStrings){
			System.out.println(str);
		}
	}
	
}
