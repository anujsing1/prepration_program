package com.groupon;

import java.util.ArrayList;
import java.util.List;
import java.util.Stack;

public class Node {
	private int value;
	private Node left;
	private Node right;
	private static Node rootNode = null;
	
	public Node(int value) {
		this.value = value;
	}
	
	/**
	 * @return the value
	 */
	public int getValue() {
		return value;
	}
	/**
	 * @param value the value to set
	 */
	public void setValue(int value) {
		this.value = value;
	}
	/**
	 * @return the left
	 */
	public Node getLeft() {
		return left;
	}
	/**
	 * @param left the left to set
	 */
	public void setLeft(Node left) {
		this.left = left;
	}
	/**
	 * @return the right
	 */
	public Node getRight() {
		return right;
	}
	/**
	 * @param right the right to set
	 */
	public void setRight(Node right) {
		this.right = right;
	}

	static void inorder(Node o) {
		Stack<Node> s = new Stack<Node>();
		s.push(o);
		Node tempNode = o;
		while (null != s || null != tempNode) {
			if(s.isEmpty()){
				break;
			}
			if (tempNode.left != null) {
				s.push(tempNode.left);
				tempNode = tempNode.left;
			} else {
				Node n = s.pop();
				System.out.print(n.getValue()+", ");
				if (n.right != null) {
					tempNode = n.right;
					s.push(tempNode);
				}
			}
		}
	}
	
	static void insertRec(Node parentNode, Node newNode){
		if (null == parentNode){
			rootNode = newNode;
		}
		else {
			Boolean left=null;
			while(true){
				if(parentNode.value > newNode.value){
					if (null == parentNode.getLeft()){
						left = true;
						break;
					}
					parentNode = parentNode.getLeft();
				}
				else if(parentNode.value < newNode.value){
					if (null == parentNode.getRight()){
						left = false;
						break;
					}
					parentNode = parentNode.getRight();
				}
				else {
					left = null;
					break;
				}
			}
			if (null == left){
			}
			else if(left)
				parentNode.left = newNode;
			else if(!left)
				parentNode.right = newNode;
		}
	}
	
	static void inorderTraversal(Node rootNode){
		List<Integer> inorder = new ArrayList<Integer>();
		Stack<Node> stack = new Stack<Node>();
		Node node = rootNode;
		
		while(node.left != null){
			stack.push(node);
			node = node.left;
		}
		while(stack.size() > 0){
			node = stack.pop();
			inorder.add(node.value);
			while(node.right != null){
				node = node.right;
				while(node.left!=null){
					stack.push(node);
					node = node.left;
				}
			}
		}
		for(Integer in : inorder){
			System.out.print(in +", ");
		}
	}
	
	static void inorderRecu(Node parentNode){
		if(parentNode == null){
			return;
		}
		inorderRecu(parentNode.getLeft());
		System.out.print(parentNode.getValue()+", ");
		inorderRecu(parentNode.getRight());
	}
	
	static void preorderRecu(Node parentNode){
		if(parentNode == null){
			return;
		}
		System.out.print(parentNode.getValue()+", ");
		preorderRecu(parentNode.getLeft());
		preorderRecu(parentNode.getRight());
	}
	
	static void postorderRecu(Node parentNode){
		if(parentNode == null){
			return;
		}
		postorderRecu(parentNode.getLeft());
		postorderRecu(parentNode.getRight());
		System.out.print(parentNode.getValue()+", ");
	}
	
	static void searchNode(int val){
		if(rootNode == null){
			return;
		}
		Node newNode = rootNode;
		while(null != newNode){
			if(val == newNode.getValue()){
				System.out.println("Element Found");
				break;
			}
			else if(val <newNode.getValue()){
				newNode = newNode.getLeft();
			}
			else if(val > newNode.getValue()){
				newNode = newNode.getRight();
			}
		}
	}
	
	public static void main(String[] args) {
		Node n1 = new Node(10);
		Node n2 = new Node(5);
		Node n3 = new Node(7);
		Node n4 = new Node(1);
		Node n5 = new Node(14);
		Node n6 = new Node(13);
		Node n7 = new Node(17);
		Node n8 = new Node(15);
		
		insertRec(rootNode, n1);
		insertRec(rootNode, n2);
		insertRec(rootNode, n3);
		insertRec(rootNode, n4);
		insertRec(rootNode, n5);
		insertRec(rootNode, n6);
		insertRec(rootNode, n7);
		insertRec(rootNode, n8);
		searchNode(12);
//		inorderTraversal(rootNode);
		System.out.println();
		inorder(rootNode);
		System.out.println();
		inorderRecu(rootNode);
		System.out.println();
		preorderRecu(rootNode);
		System.out.println();
		postorderRecu(rootNode);
	}
}
